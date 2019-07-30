// This file is needed in order allow Firefox to open file:// links
// The URL will need to be adjusted as appropriate on all clients that
// need to access the Admin tool
user_pref("capability.policy.policynames", "nrqz_admin");
user_pref("capability.policy.nrqz_admin.sites", "http://galileo:9005");
user_pref("capability.policy.nrqz_admin.checkloaduri.enabled", "allAccess");
