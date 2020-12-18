# -*- coding: utf-8 -*-

from odoo import models, fields, multi_process,api, _
from odoo.exceptions import ValidationError

# from pyfcm import FCMNotification

from datetime import datetime

import logging
_logger = logging.getLogger(__name__)

class serviceTms(models.Model):
    _name = 'services.tms'
    _description = 'Services of Transport Manager System'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    #Name and Sequence
    name = fields.Char(string="N° de Servicio", copy=False, readonly=True) 
    label_service = fields.Char(string="Nombre de Servicio", required=True)

    # N° Reference
    n_ref = fields.Char(string="Numero de Referencia")
    
    # Dates
    date_start = fields.Datetime(string="Fecha Inicial", default=fields.Datetime.now, required=True)
    date_stop = fields.Datetime(string="Fecha Final", default=fields.Datetime.now, required=True)
    
    # Odometer
    ids_odometer = fields.One2many('odometer.services.tms', 'ref_services', ondelete="cascade") 
    odo_total = fields.Integer(compute="_odo_total", string="Odometro Total")
    
    #Assignments
    employee = fields.Many2many('hr.employee', string="Empleado")
    fleet = fields.Many2one('fleet.vehicle', string="Tractor")
    fleet_add = fields.Many2one('fleet.vehicle', string="Acoplado")
    
    #Outsourced
    employee_third = fields.Many2one('employee.third.tms', string="Empleado Tercerizado")
    fleet_third = fields.Many2one('fleet.third.tms', string="Tractor Tercerizado")
    fleet_add_third = fields.Many2one('fleet.third.tms', string="Acoplado - Tercerizado")
    
    
    # Origin and Destination
    location_load = fields.Many2many('places.tms', 'ref_service_load',string="Localidad de Carga", required=True)
    location_download = fields.Many2many('places.tms', 'ref_service_download',string="Localidad de Descarga", required=True)
    
    #Note
    note = fields.Text(string="Nota")
    
    #Customer
    customer = fields.Many2one('res.partner', string="Cliente", required=True)
    
    #Supplier
    supplier = fields.Many2one('res.partner', string="Proveedor")
    
    #Outsourced service
    outsourced_service = fields.Boolean(string="Servicio Tercerizado", default=False)
    
    # Campos de estados
    state = fields.Selection([
        ('draft','Borrador'),
        ('confirmed','Confirmado'),
        ('finalized','Finalizado'),
        ('cancelled','Cancelado')], string="Estado", default="draft")
        
    # Relationship with document of service
    lst_documents = fields.One2many('document.services.tms', 'ref_services', string="Documentos", ondelete="cascade")
    state_document = fields.Boolean(default=False, string="Estado de Documentos", invisible=True, compute="_state_documents")

    # Relacion con gastos
    expense_orders_ids = fields.One2many('purchase.order', 'service_id', string="Gastos")
    total_expenses = fields.Integer(compute='_get_total_expenses', store=False)
    
    # Relacion con compras
    purchase_orders_ids = fields.One2many('purchase.order', 'service_id', string="Compras")
    total_purchases = fields.Integer(compute='_get_total_purchases', store=False)
    state_inv_p = fields.Boolean(compute="_state_inv_p", string="Estado de Fact de Proveedor")

    # Relacion con ventas
    sale_order_ids = fields.One2many('sale.order', 'service_id', 'Ventas')
    total_sales = fields.Integer(compute='_get_total_sales', store=False) 
    state_inv_s = fields.Boolean(compute="_state_inv_s", default=False, string="Estado de Fact de Proveedor")
    
    residual = fields.Float(string="Residual (Sin Impuestos)", compute="get_residual")
    
    state_invoice = fields.Boolean(string="Estado Facturación", default=False)

    @api.onchange('date_stop')
    def _date_stop_less(self):
        if self.date_stop < self.date_start:
            raise ValidationError("The end date is cannot be less than the start date")
            
    def _odo_total(self):
        self.odo_total = 0
        if len(self.ids_odometer) > 0:
            
            for obj in self.ids_odometer:
                self.odo_total += obj.odo_total
    
    # #Create sequence of services.
    @api.model
    def create(self,vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('services.tms') or _('New') + ' '
        res = super(serviceTms, self).create(vals)
        return res

    @api.depends('outsourced_service')
    def _get_total_purchases(self):
        if self.outsourced_service == True:
            self.total_purchases = sum(order.amount_untaxed for order in self.purchase_orders_ids.filtered(lambda s: s.state in ('purchase')))
        else: 
            self.total_purchases = 0  
            
    def act_show_purchases(self):  
        action = self.env.ref('purchase.purchase_form_action')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'view_mode': action.view_mode,
            'target': action.target,
            'res_model': action.res_model,
            'context': {
                'default_partner_id': self.supplier.id,
                'default_service_id': self.ids[0],
                'default_date_order': self.date_start,
                'default_date_planned': self.date_start
            }
        }
        result['domain'] = "[('id','in',[" + \
            ','.join(map(str, self.purchase_orders_ids.ids))+"])]"
        return result
    
    # State purchase invoice
    def _state_inv_p(self):
        for fact_c in self:
            if fact_c.outsourced_service == True:
                fact_c.state_inv_p = False
                flag = False
                for obj in fact_c.purchase_orders_ids:
                    if obj.invoice_count == 0:
                        flag = True
                    else:
                        fact_c.state_inv_p = True
                        if fact_c.state_document == True and fact_c.state_inv_s == True and fact_c.state_inv_p == True:
                            fact_c.state_invoice = True
                        else:
                            fact_c.state_invoice = False         
                if flag == True:
                    fact_c.state_inv_p = False
            else: 
                fact_c.state_inv_p = True
                if fact_c.state_document == True and fact_c.state_inv_s == True and fact_c.state_inv_p == True:
                    fact_c.state_invoice = True
                else:
                    fact_c.state_invoice = False
                
    
    def _get_total_expenses(self):
        self.total_expenses = sum(order.amount_untaxed for order in self.expense_orders_ids.filtered(lambda s: s.state in ('purchase') and s.es_gasto == True))
            
            
    def act_show_expenses(self, context=None):
        action = self.env.ref('purchase.purchase_form_action')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'view_mode': action.view_mode,
            'target': action.target,
            'res_model': action.res_model,
            'context': {
                'default_service_id': self.ids[0],
                'default_date_order': self.date_start,
                'default_validity_date': self.date_start,
                'default_es_gasto': True
            }
        }
        result['domain'] = "[('id','in',[" + \
            ','.join(map(str, self.expense_orders_ids.ids))+"]), ('es_gasto', '=', True)]"
        return result
            
    
    
    def _get_total_sales(self):
        self.total_sales = sum(order.amount_untaxed for order in self.sale_order_ids.filtered(lambda s: s.state in ('sale')))
    
    # Funcion que redirecciona a la orden de venta, llevando el id de este servicio en particular y añadiendolo a la orden de vente, asi tenemos una relacion entre ellos
    def act_show_sales(self, context=None):
        action = self.env.ref('sale.action_orders')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'view_mode': action.view_mode,
            'target': action.target,
            'res_model': action.res_model,
            'context': {
                'default_partner_id': self.customer.id,
                'default_service_id': self.ids[0],
                'default_date_order': self.date_start,
                'default_validity_date': self.date_start
            }
        }
        result['domain'] = "[('id','in',[" + \
            ','.join(map(str, self.sale_order_ids.ids))+"])]"
        return result
            
            

    # State sale invoice
    def _state_inv_s(self):
        for state_s in self:
            state_s.state_inv_s = False
            flag = False
            for obj in state_s.sale_order_ids:
                if obj.invoice_count == 0:
                    flag = True
                else:
                    state_s.state_inv_s = True
                    if state_s.state_document == True and state_s.state_inv_s == True and state_s.state_inv_p == True:
                        state_s.state_invoice = True
                    else:
                        state_s.state_invoice = False
            if flag == True:
                state_s.state_inv_s = False
    
    # Vemos si el servicio tiene remitos registrados, si es asi lo tomamos como un valor completo.
    @api.onchange('lst_documents')
    def _state_documents(self):
        for state_d in self:
            if len(state_d.lst_documents) >= 1:
                state_d.state_document = True
                if state_d.state_document == True and state_d.state_inv_s == True and state_d.state_inv_p == True:
                    state_d.state_invoice = True
                else:
                    state_d.state_invoice = False
            else:
                state_d.state_document = False
                
    @api.depends('total_sales', 'total_purchases')
    def get_residual(self):
        self.residual = self.total_sales - (self.total_purchases + self.total_expenses)

                
    #Status
    def status_confirmed(self):
        self.state = 'confirmed'

    def status_draft(self):
        self.state = 'draft'

    def status_finalized(self):
        self.state = 'finalized'
        
    def status_cancelled(self):
        self.state = 'cancelled'
        
    def return_action_to_open_document(self):
        self.ensure_one()
        xml_id = self.env.context.get('xml_id')
        if xml_id:
            res = self.env['ir.actions.act_window'].for_xml_id('tms', xml_id)
            res.update(
                context=dict(self.env.context, default_ref_services=self.id, group_by=False),
                domain=[('ref_services', '=', self.id)]
            )
            return res
        return False
    
class documentServiceTms(models.Model):
    _name = 'document.services.tms'

    name = fields.Char(string="Numero de Documento")
    ref_services = fields.Many2one('services.tms', invisible=True, string="Referencia del Servicio")
    n_ref = fields.Char(compute="_get_n_ref", string="Numero de Referencia")
    document_pdf = fields.Binary(string="Archivo", help="En lo posible colocar archivos inferior a 2 MB, este campo solo es para alguna imagen o documento simple")
    document_pdf_filename = fields.Char(string="Nombre")
    note = fields.Text(string="Nota")
    
    doc_service_attachment_id = fields.Many2many('ir.attachment', 'doc_attach_service_rel', 'doc_id', 'attach_id3', string="Adjunto",
                                        help='You can attach the copy of your document', copy=False)
    def _get_n_ref(self):
        for obj in self:
            obj.n_ref = obj.ref_services.n_ref
            
            
class odometerServiceTms(models.Model):
    _name = 'odometer.services.tms'
    _rec_name = 'odo_total'

    name = fields.Many2one('fleet.vehicle', string="Flota")
    employee = fields.Many2one('hr.employee', string="Empleado")
    ref_services = fields.Many2one('services.tms', invisible=True, string="Referencia del Servicio")
    date = fields.Date(string="Fecha")
    odo_start = fields.Integer(string="Inicio")
    odo_end = fields.Integer(string="Final")
    odo_total = fields.Integer(string="Total", compute="_get_total")
    note = fields.Text(string="Nota")


                
    def _get_total(self):
        for obj in self:
            obj.odo_total = obj.odo_end - obj.odo_start            
        
class ServicesDocumentAttachment(models.Model):
    _inherit = 'ir.attachment'

    doc_attach_service_rel = fields.Many2many('document.services.tms', 'doc_attachment_id', 'attach_id3', 'doc_id',
                                    string="Adjunto", invisible=1)
            
    
class saleOrderInherit(models.Model):
    _inherit = 'sale.order'

    service_id = fields.Many2one('services.tms', string="Servicio N°", required=False)
    
class purchaseOrderInherit(models.Model):
    _inherit = 'purchase.order'

    service_id = fields.Many2one('services.tms', string="Servicio N°", required=False)
    
    es_gasto = fields.Boolean(string="Es gasto?")
    
