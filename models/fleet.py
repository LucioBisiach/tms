
# -*- coding: utf-8 -*-


from odoo import api, fields, models, _

from datetime import datetime

import time

import logging
_logger = logging.getLogger(__name__)


class inheritEmployeeTms(models.Model):
    _inherit = 'fleet.vehicle'
    
    qty_ejes = fields.Char(string="Cant. Ejes")
    
    ultimo_odometro = fields.Integer(string="Ultimo Odometro", compute="_get_ultimo_odometro", default=0)
    
    cuit_registro = fields.Char(sstring="CUIT Registro")
        
    maximo_permitido = fields.Float(string="Rendimiento Max. Permitido")

    def _get_ultimo_odometro(self):
        for obj in self:
            obj.ultimo_odometro = 0
            odo_max_combustible_temp = 0
            odo_maximo_servicios_temp = 0
            odometros_combustible_filtrados = obj.env['combustible.fleet.tms'].search([('name', 'in', obj.ids)])
            odometros_servicios_filtrados = obj.env['odometer.services.tms'].search([('name', 'in', obj.ids)])
            # Odometro maximo de cargas de combustible
            if len(odometros_combustible_filtrados) > 0:
                odo_maximo_combustible = max(odometros_combustible_filtrados, key=lambda o: o.odometro)
                odo_max_combustible_temp = odo_maximo_combustible.odometro
                # _logger.info("Odomtro combustible filtrado %s", odo_max_combustible_temp)
            else:
                obj.ultimo_odometro = 0
            # Odometro maximo de servicios
            if len(odometros_servicios_filtrados) > 0:
                odo_maximo_servicios = max(odometros_servicios_filtrados, key=lambda o: o.odo_end)
                odo_maximo_servicios_temp = odo_maximo_servicios.odo_end
                # _logger.info("Odomtro servicios filtrado %s", odo_maximo_servicios_temp)
            else:
                obj.ultimo_odometro = 0
            obj.ultimo_odometro = max(odo_maximo_servicios_temp, odo_max_combustible_temp)


# Mostrar la patente en lugar de todo el choclo que muestra 
    def name_get(self):
        res = []
        for field in self:
            res.append((field.id, '%s' % (field.license_plate)))
        return res       
    
    
    def return_action_to_open(self):
        self.ensure_one()
        xml_id = self.env.context.get('xml_id')
        if xml_id:
            res = self.env['ir.actions.act_window'].for_xml_id('tms', xml_id)
            res.update(
                context=dict(self.env.context, default_name=self.id, group_by=False),
                domain=[('name', '=', self.id)]
            )
            return res
        return False
    
    def return_action_to_open_service(self):
        self.ensure_one()
        xml_id = self.env.context.get('xml_id')
        if xml_id:
            res = self.env['ir.actions.act_window'].for_xml_id('tms', xml_id)
            res.update(
                context=dict(self.env.context, default_fleet=self.id, group_by=False),
                domain=[('fleet', '=', self.id)]
            )
            return res
        return False


class combustibleFleetVehicle(models.Model):
    _name = 'combustible.fleet.tms'
    _description = 'registro de combustible'
    
    name = fields.Many2one('fleet.vehicle', string="Vehículo")
    date = fields.Date(string="Fecha")
    odometro = fields.Integer(string="Odometro")
    litros = fields.Float(string="Litros")
    rendimiento = fields.Float(string="Rendimiento")
    maximo_permitido = fields.Float(string="Rendimiento Max. Permitido", compute="_get_rendimiento_permitido")
    distancia_recorrida = fields.Integer(string="Distancia Recorrida")
    
    tiene_documento = fields.Boolean(string="Tiene documento?", default=False)
    factura_adjunta = fields.Many2one('account.move', context={'default_type': 'in_invoice'})
    
        
    @api.depends('name')
    def _get_rendimiento_permitido(self):
        for obj in self:
            obj.maximo_permitido = obj.name.maximo_permitido
    
    @api.depends('odometro')
    def get_calcular_rendimiento(self):
        lst_combustible_filtrada = self.search([('name', 'in', self.name.ids), ('odometro', '<', self.odometro)])
        if len(lst_combustible_filtrada) > 0:
            maximo = max(lst_combustible_filtrada, key=lambda o: o.odometro)
            max_valor_a_comparar = maximo.odometro
            self.distancia_recorrida = self.odometro - max_valor_a_comparar
            self.rendimiento = (self.litros * 100) / self.distancia_recorrida
        else:
            max_valor_a_comparar = 0
            
            
        

