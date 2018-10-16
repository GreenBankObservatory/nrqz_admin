# from django.forms import ModelForm
# from submission.models import Submission, Antenna


# class SubmissionForm(ModelForm):
#     class Meta:
#         model = Submission
#         fields = (
#             "applicant",
#             "contact",
#             "comments",
#             "sgrs_notified",
#             "attachments",
#             "facilities",
#         )


# class AntennaForm(ModelForm):
#     class Meta:
#         model = Antenna
#         fields = (
#             "freq_low",
#             "freq_high",
#             "bandwidth",
#             "max_output",
#             "lat",
#             "long",
#             "amsl",
#             "agl",
#             "gain",
#             "model_num",
#             "call_sign",
#             "system_loss",
#             "mechanical_downtilt",
#             "electrical_downtilt",
#             "fcc_file_number",
#             "num_transmitters",
#             "num_pols_with_feed_power",
#             "technology",
#             "technology_other",
#             "uses_split_sectorization",
#             "uses_cross_polarization",
#         )


# from django.forms import modelformset_factory, inlineformset_factory

# AntennaFormSet = modelformset_factory(Antenna, form=AntennaForm)
