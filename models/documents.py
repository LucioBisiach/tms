# -*- coding: utf-8 -*-

from odoo import models, fields, multi_process,api, _
from odoo.exceptions import ValidationError

# from pyfcm import FCMNotification

from datetime import datetime, date, timedelta

import logging
_logger = logging.getLogger(__name__)

class expiryDocumentsTms(models.Model):
    _name = 'expiry.documents.tms'
    _description = ''

    name = fields.Char(string="Documento", required=True, copy=False)
    
    tipe = fields.Selection([
        ('company','Compañia'),
        ('employee','Empleado'),
        ('fleet','Flota')], string="Tipo", required=True)
    
    fleet = fields.Many2one('fleet.vehicle', string="Vehiculo")
    
    employee = fields.Many2one('hr.employee', string="Empleado")
    
    frecuencia_notifiacion = fields.Selection([
        ('everyday', 'Todos los días'),
        ('expiry_date', 'Dia del Vencimiento')], string="Frecuencia Notificación")
    
    days_notification = fields.Integer(string="Días de aviso")
    
    notificacion_compania = fields.Char(string="Notificar a:")
    
    
    @api.onchange('tipe')
    def _hide_field(self):
        if self.tipe == 'company':
            self.fleet = ''
            self.employee = ''
        if self.tipe == 'employee':
            self.fleet = ''
        if self.tipe == 'employee':
            self.employee = ''
            
            
    list_expiry_document = fields.One2many('list.expiry.documents.tms', 'name', string="Vencimiento", ondelete="cascade")
    
class ExpiryDocumentAttachment(models.Model):
    _inherit = 'ir.attachment'

    doc_attach_expiry_rel = fields.Many2many('list.expiry.documents.tms', 'expiry_doc_attachment_id', 'attach_id3', 'doc_id',
                                    string="Adjunto", invisible=1)

class listExpiryDocumentsTms(models.Model):
    _name = 'list.expiry.documents.tms'
    _description = ''
    
    name = fields.Many2one('expiry.documents.tms', string="Descripción", readonly=True)
    date_stop = fields.Date(string="Fecha de Vencimiento")
    
    days_remaining = fields.Integer(string="Días Restantes", compute="_get_days_remaining")
    
    state = fields.Selection([
        ('updated','ACTUALIZADO'),
        ('next','PROXIMO A VENCER'),
        ('defeated','VENCIDO'),
        ('today','VENCE HOY!'),
        ('draft','BORRADOR')], string="Estado", compute="_get_status")
    
    archived = fields.Boolean(string="Archivado")
    
    doc_expiry_attachment_id = fields.Many2many('ir.attachment', 'doc_attach_expiry_rel', 'doc_id', 'attach_id3', string="Adjunto",
                                        help='You can attach the copy of your document', copy=False)
    
    tipe = fields.Char(string="Tipo", invisible=True)
    document_name = fields.Char(string="Nombre Doc", compute="_get_document_name")
    
    def _get_document_name(self):
        for rec in self:
            if rec.name.tipe == 'fleet':
                rec.document_name = rec.name.fleet.name
            if rec.name.tipe == 'employee':
                rec.document_name = rec.name.employee.name
            if rec.name.tipe == 'company':
                rec.document_name = 'Company'
            
    
    
    def _get_status(self):
        for rec in self:
            rec.tipe = rec.name.tipe
            if rec.date_stop:
                if rec.days_remaining <= rec.name.days_notification and rec.days_remaining > 0:
                    rec.state = 'next'
                if rec.days_remaining == 0:
                    rec.state = 'today'
                if rec.days_remaining < 0:
                    rec.state = 'defeated'
                if rec.days_remaining > rec.name.days_notification:
                    rec.state = 'updated'
            else:
                rec.state = 'draft'
    
    
    @api.depends('date_stop')
    def _get_days_remaining(self):
        for rec in self:
            if rec.date_stop:
                expiry_date = rec.date_stop
                today = datetime.now().strftime('%Y-%m-%d')
                number_days = (
                    fields.Date.from_string(expiry_date) -
                    fields.Date.from_string(today)).days
                if number_days > 0:
                    rec.days_remaining = number_days
                else:
                    rec.days_remaining = number_days
            else:
                rec.days_remaining = 0
                
                
    def notificacion_vencimiento(self):
        vencimientos_no_archivados = self.search([('archived','!=','True')])
        now = datetime.now() 
        date_now = now.date()
        for i in vencimientos_no_archivados:
            
            if i.date_stop:
                # Vencimientos proximo a vencer, con la alerta de todos los dias
                if i.name.frecuencia_notifiacion == 'everyday' and i.state == 'next' and i.name.tipe == 'employee':
                    contenido_email = "  Hola  " + i.name.employee.name + " , Tu documento  " + i.name.name + " vence el: " +  str(i.date_stop) + ". Te quedan " + str(abs(i.days_remaining)) + " días para renovarlo. Porfavor actualizalo lo antes posible."
                    datos_email = {
                        'subject': _('Documento-%s %sproximo a vencer %s') % (i.name.name, i.name.employee.name, i.date_stop),
                        'author_id': self.env.company.id,
                        'body_html': contenido_email,
                        'email_to': i.name.employee.work_email,
                    }
                    self.env['mail.mail'].create(datos_email).send()
                    
                elif i.name.frecuencia_notifiacion == 'everyday' and i.state == 'next' and i.name.tipe == 'fleet':
                    contenido_email = "  Hola, Tu documento  " + i.name.name + " correspondiente al vehículo "+ i.name.fleet.license_plate + " vence el: " +  str(i.date_stop) + ". Te quedan " + str(abs(i.days_remaining)) + " días para renovarlo. Porfavor actualizalo lo antes posible."
                    datos_email = {
                        'subject': _('Documento-%s %s proximo a vencer %s') % (i.name.name, i.name.fleet.license_plate, i.date_stop),
                        'author_id': self.env.company.id,
                        'body_html': contenido_email,
                        'email_to': i.name.fleet.email_notificacion,
                    }
                    self.env['mail.mail'].create(datos_email).send()
                    
                elif i.name.frecuencia_notifiacion == 'everyday' and i.state == 'next' and i.name.tipe == 'company':
                    contenido_email = "  Hola, Tu documento  " + i.name.name + " vence el: " +  str(i.date_stop) + ". Te quedan " + str(abs(i.days_remaining)) + " días para renovarlo. Porfavor actualizalo lo antes posible."
                    datos_email = {
                        'subject': _('Documento-%s proximo a vencer %s') % (i.name.name, i.date_stop),
                        'author_id': self.env.company.id,
                        'body_html': contenido_email,
                        'email_to': i.name.notificacion_compania,
                    }
                    self.env['mail.mail'].create(datos_email).send()
                    
                # Vencimientos vence hoy, con la alerta de todos los dias
                elif i.name.frecuencia_notifiacion == 'everyday' and i.state == 'today' and i.name.tipe == 'employee':
                    contenido_email = "  Hola  " + i.name.employee.name + " , Tu documento  " + i.name.name + " vence hoy ! " +  str(i.date_stop) + ". Te quedan " + ". Porfavor actualizalo lo antes posible."
                    datos_email = {
                        'subject': _('Documento-%s %sproximo a vencer %s') % (i.name.name, i.name.employee.name, i.date_stop),
                        'author_id': self.env.company.id,
                        'body_html': contenido_email,
                        'email_to': i.name.employee.work_email,
                    }
                    self.env['mail.mail'].create(datos_email).send()
                    
                elif i.name.frecuencia_notifiacion == 'everyday' and i.state == 'today' and i.name.tipe == 'fleet':
                    contenido_email = "  Hola, Tu documento  " + i.name.name + " correspondiente al vehículo "+ i.name.fleet.license_plate + ". Porfavor actualizalo lo antes posible."
                    datos_email = {
                        'subject': _('Documento-%s %s vence hoy! %s') % (i.name.name, i.name.fleet.license_plate, i.date_stop),
                        'author_id': self.env.company.id,
                        'body_html': contenido_email,
                        'email_to': i.name.fleet.email_notificacion,
                    }
                    self.env['mail.mail'].create(datos_email).send()
                    
                elif i.name.frecuencia_notifiacion == 'everyday' and i.state == 'today' and i.name.tipe == 'company':
                    contenido_email = "  Hola, Tu documento  " + i.name.name + " vence hoy ! " +  str(i.date_stop) + ". Porfavor actualizalo lo antes posible."
                    datos_email = {
                        'subject': _('Documento-%s vence hoy! %s') % (i.name.name, i.date_stop),
                        'author_id': self.env.company.id,
                        'body_html': contenido_email,
                        'email_to': i.name.notificacion_compania,
                    }
                    self.env['mail.mail'].create(datos_email).send()
                    
                # Vencimientos vencido, con la alerta de todos los dias
                elif i.name.frecuencia_notifiacion == 'everyday' and i.state == 'defeated' and i.name.tipe == 'employee':
                    contenido_email = "  Hola  " + i.name.employee.name + " , Tu documento  " + i.name.name + " se encuentra vencido. Expiró el: " +  str(i.date_stop) + ". Porfavor actualizalo lo antes posible."
                    datos_email = {
                        'subject': _('Documento-%s - %s Vencido el: %s') % (i.name.name, i.name.employee.name, i.date_stop),
                        'author_id': self.env.company.id,
                        'body_html': contenido_email,
                        'email_to': i.name.employee.work_email,
                    }
                    self.env['mail.mail'].create(datos_email).send()
                    
                elif i.name.frecuencia_notifiacion == 'everyday' and i.state == 'defeated' and i.name.tipe == 'fleet':
                    contenido_email = "  Hola, Tu documento  " + i.name.name + " correspondiente al vehículo "+ i.name.fleet.license_plate + " vence hoy ! " +  str(i.date_stop) + ". Porfavor actualizalo lo antes posible."
                    datos_email = {
                        'subject': _('Documento-%s - %s Vencido el: %s') % (i.name.name, i.name.fleet.license_plate, i.date_stop),
                        'author_id': self.env.company.id,
                        'body_html': contenido_email,
                        'email_to': i.name.fleet.email_notificacion,
                    }
                    self.env['mail.mail'].create(datos_email).send()
                    
                elif i.name.frecuencia_notifiacion == 'everyday' and i.state == 'defeated' and i.name.tipe == 'company':
                    contenido_email = "  Hola, Tu documento  " + i.name.name + " venció el:  " +  str(i.date_stop) + ". Porfavor actualizalo lo antes posible."
                    datos_email = {
                        'subject': _('Documento-%s Vencido el %s') % (i.name.name, i.date_stop),
                        'author_id': self.env.company.id,
                        'body_html': contenido_email,
                        'email_to': i.name.notificacion_compania,
                    }
                    self.env['mail.mail'].create(datos_email).send()
                    
                # Vencimiento hoy con alerta de hoy

                # elif date_now == i.date_stop and i.name.frecuencia_notifiacion == 'expiry_date':