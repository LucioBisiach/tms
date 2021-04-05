

# -*- coding: utf-8 -*-


from odoo import api, fields, models, _

from datetime import datetime

from odoo.exceptions import ValidationError, UserError, MissingError

import requests
import urllib
import json

import logging
_logger = logging.getLogger(__name__)


class inheritResPartnerTms(models.Model):
    _inherit = 'res.partner'

    
    es_transportista = fields.Selection([
        ('si','Si'),
        ('no','No')], string="Es Transportista?")

    empresa_transportista = fields.Boolean(string="Empresa Transportista")

    API_BASE_URL = "https://consultapme.cnrt.gob.ar/api/"

    paut = fields.Char(string="PAUT", help="Padrón único de Transportistas", compute="_get_data_cnrt")
    n_empresa = fields.Char(string="N° de Empresa", readonly=True)
    empresa_habilitada = fields.Boolean(string="Empresa Habilitada?", default=False, readonly=True)
    
    ids_fleet_supplier = fields.Many2many('fleet.third.tms', string="Flota")
 

    @api.onchange('company_type')
    def _value_empresa_transportista(self):
        if self.company_type == 'person':
            self.empresa_transportista = False


    def _get_data_cnrt(self):
        for obj in self:
            obj.empresa_habilitada = False
            if obj.empresa_transportista == True and obj.vat:
                if obj.vat and len(obj.vat) == 11:
                    res = requests.get(obj.API_BASE_URL + "empresa_jn_habilitada/cuit/" + obj.vat + ".json")
                    # EMPRESA HABILITADA O NO SEGÚN CUIT
                    if res.status_code == 200:
                        jsonObject = res.json()
                        obj.paut = str(jsonObject['paut'])
                        obj.n_empresa = str(jsonObject['empresa_nro'])
                        # obj.name = str(jsonObject['razon_social'])
                        obj.empresa_habilitada = True
                    else:
                        obj.paut = 'CUIT no habilitado por el CNRT'
                        obj.n_empresa = 'CUIT no habilitada por el CNRT'                    
            else:
                obj.paut = ''
                obj.n_empresa = ''
                
    def get_flota_cuit(self):
        for obj in self:
            if obj.empresa_habilitada == True and obj.l10n_latam_identification_type_id.name == 'CUIT':
                    res_fleet = requests.get(obj.API_BASE_URL + "vehiculo_cargas_habilitadospordocumento/" + obj.l10n_latam_identification_type_id.name + "/" + obj.vat + ".json")
                    if res_fleet.status_code == 200:
                        #JSON DE FLOTA SEGUN CUIT
                        fleetJsonObject = res_fleet.json()
                        for data in fleetJsonObject:
                            vals= {
                                'name': data['dominio'],
                                'belonging_to': obj.id,
                                'año': data['anio_modelo'],
                                'nro_chasis': data['nro_chasis'],
                                'cant_ejes': data['cantidad_ejes'],
                                'pais': data['pais'],
                                'tipo_vehiculo': data['tipo_vehiculo'],
                                'chasis_marca': data['chasis_marca'],
                            }
                            model_fleet_third_tms = self.env['fleet.third.tms'].search([('name', '=',data['dominio'])])
                            if not model_fleet_third_tms:
                                model_fleet_third_tms.create(vals)
                            else:
                                model_fleet_third_tms.write(vals)
                                # _logger.info("Dominio ya existe %s", data['dominio'])
                    else:
                        _logger.info("404 Not found")
            else:
                _logger.info("Empresa no habilitada o Documento no valido")
        # Creamos el dominio por el cual vamos a filtrar los registros.
        fleet_domain = [
            ('belonging_to', 'in', self.ids)
        ]
        # Traemos los servicios de dicha clase y los ordenamos por los valores que querramos, en caso de querer ordenar por mas valores, seguir con una coma ingresar el campo y el orden
        fleet = self.env['fleet.third.tms'].search(fleet_domain)
        self.ids_fleet_supplier = fleet
