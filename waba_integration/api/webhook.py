import frappe
from waba_integration.whatsapp_business_api_integration.doctype.waba_whatsapp_message.waba_whatsapp_message import (
    create_waba_whatsapp_message,
    create_waba_whatsapp_contact,
    process_status_update,
)

import boot_commerce.utils as bcu

from werkzeug.wrappers import Response
import requests

@frappe.whitelist(allow_guest=True)
def handle():
    if frappe.request.method == "GET":
        return verify_token_and_fulfill_challenge()

    try:
        form_dict = frappe.local.form_dict
        messages = form_dict["entry"][0]["changes"][0]["value"].get("messages", [])
        statuses = form_dict["entry"][0]["changes"][0]["value"].get("statuses", [])
        contacts = form_dict["entry"][0]["changes"][0]["value"].get("contacts", [])
        
        for status in statuses:
            process_status_update(status)

        contact_name = None
        for contact in contacts:
            contact_name = create_waba_whatsapp_contact(contact)

        for message in messages:
            message_doc = create_waba_whatsapp_message(message)

            bcu.set_Message_Chatbot(message_doc, contact_name)

            # #Se elimina solo para las pruebas de postman
            # frappe.db.delete('WABA WhatsApp Message', message_doc)

        frappe.get_doc(
            {"doctype": "WABA Webhook Log", "payload": frappe.as_json(form_dict)}
        ).insert(ignore_permissions=True)
    except Exception:
        frappe.log_error("WABA Webhook Log Error", frappe.get_traceback())
        frappe.throw("Something went wrong")

@frappe.whitelist(allow_guest=True)
def test_handle():
    form_dict = frappe.local.form_dict
    messages = form_dict["entry"][0]["changes"][0]["value"].get("messages", [])
    statuses = form_dict["entry"][0]["changes"][0]["value"].get("statuses", [])
    contacts = form_dict["entry"][0]["changes"][0]["value"].get("contacts", [])

    for status in statuses:
        process_status_update(status)

    contact_name = None
    for contact in contacts:
        contact_name = create_waba_whatsapp_contact(contact)

    message_doc = frappe.get_doc("WABA WhatsApp Message", "2206e7691f")
    bcu.set_Message_Chatbot(message_doc, contact_name)

def verify_token_and_fulfill_challenge():
    meta_challenge = frappe.form_dict.get("hub.challenge")
    expected_token = frappe.db.get_single_value("WABA Settings", "webhook_verify_token")

    if frappe.form_dict.get("hub.verify_token") != expected_token:
        frappe.throw("Verify token does not match")

    return Response(meta_challenge, status=200)
