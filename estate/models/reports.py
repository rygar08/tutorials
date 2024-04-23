from odoo.odoo import models, api


class PropertyOffersReport(models.AbstractModel):
    _name = 'report.estate.report_property_offers'
    _description = 'Property Offers Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['estate.property'].browse(docids)
        for doc in docs:
            print(doc.id)  # This will print the ID of each document
        return {
            'doc_ids': docs.ids,
            'doc_model': 'estate.property',
            'docs': docs,
            'data': data,  # You can include additional data here
        }