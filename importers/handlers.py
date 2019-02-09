from cases.models import Attachment


def handle_case(
    row_data,
    form_map,
    data=None,
    applicant=None,
    contact=None,
    file_import_attempt=None,
    imported_by=None,
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
            form=case_form,
            row_data=row_data,
            file_import_attempt=file_import_attempt,
            imported_by=imported_by,
        )
        case_created = True

    return case, case_created


def handle_attachments(row_data, model, form_maps, file_import_attempt, imported_by):
    attachments = []
    for form_map in form_maps:
        attachment_form, conversion_errors = form_map.render(row_data.data)
        if attachment_form:
            path = attachment_form["path"].value()
            if path:
                if Attachment.objects.filter(path=path).exists():
                    attachment = Attachment.objects.get(path=path)
                    attachment_created = False
                else:
                    attachment, __ = form_map.save_with_audit(
                        form=attachment_form,
                        row_data=row_data,
                        file_import_attempt=file_import_attempt,
                        imported_by=imported_by,
                    )
                    attachment_created = True

                attachments.append((attachment, attachment_created))
                model.attachments.add(attachment)
    return attachments
