# -*- coding: utf-8 -*-

from odoo import models, fields, multi_process,api, _
from odoo.exceptions import ValidationError

# from pyfcm import FCMNotification

from datetime import datetime

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
    
    document_pdf = fields.Binary(string="Archio")
    document_pdf_filename = fields.Char(string="Nombre")
    
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
                
                
