import esperclient
import json
from esperclient.rest import ApiException

class EsperAutoAppUpdater():

    def __init__(self, host, key, eid):
        self.eid = eid
        self.configuration = esperclient.Configuration()
        self.configuration.host = f"https://{host}-api.esper.cloud/api"
        self.configuration.api_key['Authorization'] = key
        self.configuration.api_key_prefix['Authorization'] = 'Bearer'
        self.app_api_instance = esperclient.ApplicationApi(esperclient.ApiClient(self.configuration))
        self.cmd_api_instance = esperclient.CommandsApi(esperclient.ApiClient(self.configuration))
        self.dev_api_instance = esperclient.DeviceApi(esperclient.ApiClient(self.configuration))

    def get_device_guid(self, device_id):
        device_guid = None
        try:
            devices_resp = self.dev_api_instance.get_all_devices(self.eid, name=device_id, limit=1)
            if len(devices_resp.results) == 1 and devices_resp.results[0].device_name == device_id:
                device_guid = devices_resp.results[0].id
        except ApiException as e:
            print("Exception when calling get_all_devices: %s\n" % e)
        return device_guid

    def get_app_id(self, pkg):
        app_id = None
        try:
            all_apps_resp = self.app_api_instance.get_all_applications(self.eid, package_name=pkg)
            if len(all_apps_resp.results) == 1:
                app_id =  all_apps_resp.results[0].id
        except ApiException as e:
            print("Exception when calling get_all_applications: %s\n" % e)
        return app_id

    def get_latest_app_version(self, aid):
        latest_app_version = None
        try:
            app_versions_resp = self.app_api_instance.get_app_versions(aid, self.eid)
            if len(app_versions_resp.results) > 0:
                app_versions_resp.results.sort(key=lambda x: x.build_number, reverse=True)
                latest_app_version = app_versions_resp.results[0]
        except ApiException as e:
            print("Exception when calling get_app_versions: %s\n" % e)
        return latest_app_version

    def push_app_to_device(self, device_guid, app_version):
        push_successful,error = False,None
        command_args = esperclient.CommandArgs(app_version=app_version)
        command = esperclient.CommandRequest(command='INSTALL', command_args=command_args)
        try:
            api_response = self.cmd_api_instance.run_command(self.eid, device_guid, command)
            print("Push response:")
            print(api_response)
            push_successful = True
        except ApiException as e:
            print("Exception when calling run_command: %s\n" % e)
            error_json = json.loads(e.body)
            error = error_json['message']
            error = error.strip()
        return push_successful,error

    def push_latest_app_version_if_needed(self, pkg, device_id, curr_buildnumber):
        status,msg = "Suceeded",""
        application_id = self.get_app_id(pkg)
        if application_id is not None:
            print(f"Received application id from Esper]: {application_id} ({pkg})")
            latest_version = self.get_latest_app_version(application_id)
            print(f"Latest version of the app has build number: {latest_version.build_number}")
            print(f"id = {latest_version.id}")
            print(f"version_code = {latest_version.version_code}")
            print(f"created_on = {latest_version.created_on}")
            print(f"release_comments = {latest_version.release_comments}")
            latest_build_num = int(latest_version.build_number)
            curr_buildnumber = int(curr_buildnumber)
            if latest_build_num > curr_buildnumber:
                print("Update needed. Requesting update")
                dev_guid = self.get_device_guid(device_id)
                if dev_guid is not None:
                    push_ok,err = self.push_app_to_device(dev_guid, latest_version.id)
                    if not push_ok:
                        msg = f"Unable to push {pkg}. {err}"
                        status = "Failed"
                else:
                    msg = f"Unable to acquire device GUID {pkg}"
                    status = "Failed"
            else:
                msg = f"No need to update pkg {pkg}"
        else:
            msg = f"Failed to acquire application ID for pkg {pkg}"
            status = "Failed"
        
        return status,msg