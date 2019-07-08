"""High-level helper functions that handle common model import tasks"""

from cases.models import Attachment


def handle_case(
    row_data, form_map, data=None, applicant=None, contact=None, imported_by=None
):
    if data is not None:
        row = data
    else:
        row = row_data.data
    # Derive the case model (Could be Case or PCase) from the form_map
    applicant = getattr(applicant, "id", None)
    contact = getattr(contact, "id", None)
    model = form_map.form_class.Meta.model
    case_form, conversion_errors = form_map.render(
        row, extra={"applicant": applicant, "contact": contact}
    )
    if not case_form:
        return None, False
    case_num = case_form["case_num"].value()
    if model.objects.filter(case_num=case_num).exists():
        case = model.objects.get(case_num=case_num)
        case_created = False
    else:
        case, __ = form_map.save_with_audit(
            form=case_form, row_data=row_data, imported_by=imported_by
        )
        case_created = True

    return case, case_created


def get_or_create_attachment(row_data, form_map, imported_by):
    attachment = None
    attachment_created = False
    attachment_form, conversion_errors = form_map.render(row_data.data)
    if attachment_form:
        path = attachment_form["path"].value()
        if path:
            if Attachment.objects.filter(path=path).exists():
                attachment = Attachment.objects.get(path=path)
            else:
                attachment, __ = form_map.save_with_audit(
                    form=attachment_form, row_data=row_data, imported_by=imported_by
                )
                attachment_created = True

    return attachment, attachment_created


def handle_attachments(row_data, model, form_maps, imported_by):
    attachments_info = []
    for form_map in form_maps:
        attachments_info.append(
            get_or_create_attachment(row_data, form_map, imported_by)
        )

    model.attachments.add(*[info[0] for info in attachments_info if info[0]])
    return attachments_info
