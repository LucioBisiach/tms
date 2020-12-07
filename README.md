# tms
=========

Módulo para gestionar servicios de transportistas en Odoo 13

El siguiente módulo permite administrar aquellos servicios que brindan la empresas de transporte.
Algunas de la funciones principales son:
- Crear y administrar servicios propios
- Crear y administrar servicios tercerizados
- Gestionar documentación de empleados o vehículos (Vencimientos)

<h5>Verificar datos de empresas transportistas.</h5>

Al ingresar un nuevo proveedor, podemos definirlo como Empresa Transportista, si su CUIT se encuentra registrado en el CNRT (Comisión Nacional de Regulación del Transporte) el sistema nos mostrará su PAUT y su Numero de Empresa. 
También nos generará todos los vehículos asociados a ese cuit registrado con los siguientes datos:
- Dominio
- Año
- N° Chasis
- Marca
- Tipo de Vehículo


Ver https://consultapme.cnrt.gob.ar/api/doc para ver la API.

<h2>Autor</h2>
<h4>Bisiach Lucio - bisiachlucio@gmail.com</h4>
