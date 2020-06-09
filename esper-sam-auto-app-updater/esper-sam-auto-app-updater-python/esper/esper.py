import json
import time

import esperclient
from esperclient.rest import ApiException


class EsperAutoAppUpdater():

    def __init__(self, host, key, eid):
        self.eid = eid
        self.configuration = esperclient.Configuration()
        self.configuration.host = f"https://{host}-api.esper.cloud/api"
        self.configuration.api_key['Authorization'] = key
        self.configuration.api_key_prefix['Authorization'] = 'Bearer'
        self.app_api_instance = esperclient.ApplicationApi(esperclient.ApiClient(self.configuration))
        self.cmd_api_instance = esperclient.CommandsV2Api(esperclient.ApiClient(self.configuration))
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
                app_id = all_apps_resp.results[0].id
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
        command_status, error = False, None
        command_pending = True
        command_args = esperclient.V0CommandArgs(app_version=app_version)
        command_request = esperclient.V0CommandRequest(command_type='DEVICE', devices=[device_guid], command='INSTALL',
                                                       command_args=command_args, device_type='all')
        try:
            api_response = self.cmd_api_instance.create_command(self.eid, command_request)
            print("Push successful:")
            command_status = True
            command_id = api_response.id
            while command_pending:
                try:
                    # get status list for command request
                    status_api_response = self.cmd_api_instance.get_command_request_status(self.eid, command_id)
                except ApiException as e:
                    print("Exception when calling CommandsV2Api->get_command_request_status: %s\n" % e)
                    return False, "Failed to get status"

                command_state = status_api_response.results[0].state
                if command_state == 'Command Success':
                    return True, None
                elif command_state == 'Command Failure':
                    return False, "Failed to install app on device"
                elif command_state == 'Command TimeOut':
                    return False, 'No response from device'
                print("Awaiting response from device on command status")

                time.sleep(2)
        except ApiException as e:
            print("Exception when calling run_command: %s\n" % e)
            error_json = json.loads(e.body)
            error = error_json['message']
            error = error.strip()

        return command_status, error

    def push_latest_app_version_if_needed(self, pkg, device_id, curr_buildnumber):
        status, msg = "Succeeded", ""
        application_id = self.get_app_id(pkg)
        if application_id is not None:
            print(f"Received application id from Esper: {application_id} ({pkg})")
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
                    push_ok, err = self.push_app_to_device(dev_guid, latest_version.id)
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

        return status, msg
