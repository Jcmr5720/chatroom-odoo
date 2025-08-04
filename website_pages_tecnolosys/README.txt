Modulo website_pages_tecnolosys
===============================

Este modulo extiende la funcionalidad de Odoo para personalizar el sitio web de Tecnolosys.
Proporciona diferentes paginas, secciones y snippets dinamicos que permiten mostrar
productos, promociones y contenedores disenados a medida.

Aspectos clave
--------------
* Sobrescribe el controlador de la pagina principal para cargar datos propios del modulo.
* Incluye templates XML con containers y snippets para el frontend.
* Gestiona assets de estilo (SCSS) y scripts (JS) que se cargan en ``web.assets_frontend``.
* Los modelos realizan busquedas en productos y programas de lealtad para obtener
  ofertas o listas especiales que se presentan en la web.

Consideraciones
---------------
* Requiere los modulos base de ``website``, ``web_editor`` y dependencias listadas en ``__manifest__.py``.
* Algunos snippets dependen de programas de lealtad configurados previamente para
  obtener descuentos o productos destacados.
* Asegurese de publicar los productos en el sitio web y de tener cantidades disponibles
  para que se muestren correctamente en los carruseles.

  1basd2255qwea33
* Actualizacion ok