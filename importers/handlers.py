from cases.models import Attachment


def handle_case(row, form_map, applicant=None, contact=None):
    # Derive the case model (Could be Case or PCase) from the form_map
    applicant = getattr(applicant, "id", None)
    contact = getattr(contact, "id", None)
    model = form_map.form_class.Meta.model
    case_form = form_map.render(row, extra={"applicant": applicant, "contact": contact})
    case_num = case_form["case_num"].value()
    if model.objects.filter(case_num=case_num).exists():
        case = model.objects.get(case_num=case_num)
        case_created = False
    else:
        case = form_map.save(case_form)
        case_created = True

    return case, case_created


def handle_attachments(row, case, form_maps):
    attachments = []
    for form_map in form_maps:
        attachment_form = form_map.render(row)
        path = attachment_form["path"].value()
        if path:
            if Attachment.objects.filter(path=path).exists():
                attachment = Attachment.objects.get(path=path)
            else:
                attachment = form_map.save(attachment_form)

            attachments.append(attachment)
            case.attachments.add(attachment)
    return attachments
