from cases.models import Attachment


def handle_case(row, form_map, row_audit, applicant=None, contact=None):
    # Derive the case model (Could be Case or PCase) from the form_map
    applicant = getattr(applicant, "id", None)
    contact = getattr(contact, "id", None)
    model = form_map.form_class.Meta.model
    case_form, conversion_errors = form_map.render(
        row, extra={"applicant": applicant, "contact": contact}
    )
    case_num = case_form["case_num"].value()
    if model.objects.filter(case_num=case_num).exists():
        case = model.objects.get(case_num=case_num)
        case_audit = None
    else:
        case, case_audit = form_map.save_with_audit(case_form, row_audit=row_audit)

    return case, case_audit


def handle_attachments(row, case, form_maps):
    attachments = []
    for form_map in form_maps:
        attachment_form, conversion_errors = form_map.render(row)
        path = attachment_form["path"].value()
        if path:
            if Attachment.objects.filter(path=path).exists():
                attachment = Attachment.objects.get(path=path)
            else:
                attachment = form_map.save(attachment_form)

            attachments.append(attachment)
            case.attachments.add(attachment)
    return attachments
