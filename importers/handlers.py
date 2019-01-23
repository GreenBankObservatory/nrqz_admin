from cases.models import Attachment


def handle_case(
    row_data, form_map, applicant=None, contact=None, file_import_attempt=None
):
    row = row_data.data
    # Derive the case model (Could be Case or PCase) from the form_map
    applicant = getattr(applicant, "id", None)
    contact = getattr(contact, "id", None)
    model = form_map.form_class.Meta.model
    case_form, conversion_errors = form_map.render(
        row, extra={"applicant": applicant, "contact": contact}
    )
    if not case_form:
        return None, None
    case_num = case_form["case_num"].value()
    if model.objects.filter(case_num=case_num).exists():
        case = model.objects.get(case_num=case_num)
        case_audit = None
    else:
        case, case_audit = form_map.save_with_audit(
            form=case_form, row_data=row_data, file_import_attempt=file_import_attempt
        )

    return case, case_audit


def handle_attachments(row_data, case, form_maps, file_import_attempt=None):
    attachments = []
    for form_map in form_maps:
        attachment_form, conversion_errors = form_map.render(row_data.data)
        if attachment_form:
            path = attachment_form["path"].value()
            if path:
                if Attachment.objects.filter(path=path).exists():
                    attachment = Attachment.objects.get(path=path)
                else:
                    attachment = form_map.save(attachment_form)

                attachments.append(attachment)
                case.attachments.add(attachment)
    return attachments
