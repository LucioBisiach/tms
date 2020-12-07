# -*- coding: utf-8 -*-

from odoo import models, fields, api

from datetime import datetime

class placesTms(models.Model):
    _name = 'places.tms'
    _description = 'Places of location load/download in services'


    name = fields.Char(string="Localidad")
    country_id = fields.Many2one('res.country', string="País")
    state_id = fields.Many2one('res.country.state', string="Provincia", domain="[('country_id', '=?', country_id)]")
    

    url_googlemaps = fields.Char(string="Link Google Maps")
    
    ref_service_load = fields.Many2one('service.services', invisible=True, readonly=True)
    ref_service_download = fields.Many2one('service.services', invisible=True, readonly=True)
    

class employeeThirdTms(models.Model):
    _name = 'employee.third.tms'
    _description = 'Outsourced employees'
    
    
    name = fields.Char(string='Nombre')
    phone = fields.Char(string='Telefono')
    indetification_number = fields.Char(string='DNI/CUIL')
    email = fields.Char(string='Mail')
    belonging_to = fields.Many2one('res.partner', string='Pertenece a:')

    note = fields.Text(string='Nota')
    
    
class fleetThirdTms(models.Model):
    _name = 'fleet.third.tms'
    
    name = fields.Char(string='Patente')
    belonging_to = fields.Many2one('res.partner', string='Pertenece a:')
    año = fields.Char(string="Año")
    nro_chasis = fields.Char(string="N° Chasis")
    cant_ejes = fields.Integer(string="Cant. Ejes")
    pais = fields.Char(string="País")
    tipo_vehiculo = fields.Selection([
        ('TRACTOR','Tractor'),
        ('SEMIRREMOLQUE','Semirremolque'),
        ('CAMIÓN','Camión'),
        ('ACOPLADO','Acoplado'),
        ('BATEA','Batea'),
        ('FURGÓN','Furgón'),
        ('CAMIONETA','Camioneta'),
        ('CARRETON','Carretón'),], string="Tipo")
    
    chasis_marca = fields.Char(string="Marca")
    permiso_origen = fields.Many2many('permission.fleet.third.tms', string="P. INT (Origen)")
    nro_ruta = fields.Char(string="RUTA")
    # permiso_destino = fields.Many2many('permission.fleet.third.tms', string="P. INT (Destino)")

    
    note = fields.Text(string='Nota')
    
class permissionCountryFleetThirdTms(models.Model):
    _name = 'permission.fleet.third.tms'
    
    name = fields.Char(string="País")
    
    
    