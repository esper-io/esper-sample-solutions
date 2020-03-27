# esper-sam-auto-app-updater

One of our customers is trying to solve an interesting problem: devices provisioned by them would sit in a switched-off state on a shelf for long duration, before their customers would be using the units. While the units were on the shelf, the customer would update their apps by several versions. As a result, when their end customers would switch on the units after a long time, they would have older versions of their apps.

The ask was to come up with a way to programmatically push the latest version of the app, as soon as the unit came online.

This solution creates an AWS lambda with an API gateway in front of it. The customer's app calls this lambda from their app and passes it the build number ([`versionCode`](https://developer.android.com/studio/publish/versioning)) of the app. The lambda talks to Esper and determines if there's a more recent version of the app uploaded to Esper. If there is, it will send a message to Esper to update the device with the latest version of the app.

## Prerequisites

* Clone the Repository to your PC:

```bash
git clone git@github.com:esper-io/esper-api-sample-code.git
```

or

```bash
git clone https://github.com/esper-io/esper-api-sample-code.git
```

* Ensure you have an environment with [Python 3.7](https://www.python.org/downloads/) available.

* Ensure you have the [SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html) installed.

* Ensure you have [Docker](https://hub.docker.com/search/?type=edition&offering=community) installed.

## Usage

Ensure you are in the `esper-sam-auto-app-updater` directory

Modify the `samconfig.toml` file and change the `stack_name`, `s3_bucket`, `s3_prefix`, `region` to suit your infrastructure setup.

In all the following commands, replace:

* `x` with the endpoint name. If the URL for your Esper endpoint is `foo.esper.cloud`, use `foo` here.
* `y` with the API Key from your console.
* `z` with the enterprise ID from your console.

The POST payload should always have this data:

```json
  {
    "device_id":"<e.g. ESP-DMO-ABCD>",
    "pkg":"<e.g. io.esper.foo>",
    "build_number":"<e.g. 29>"
  }
```

Responses from the Lambda:

Successfully pushed the newest app to the device:
```json
{"status": "Request succeded", "msg": ""}
```

Application version already exists on the device:
```json
{"status": "Request failed", "msg": "Unable to push com.cpuid.cpu_z. App already exists on device"}
```

Application version already exists on the device:
```json
{"status": "Request failed", "msg": "Unable to push com.cpuid.cpu_z. App already exists on device"}
```

If `status` is `Request succeded` you are all good.

### Try this locally

To build locally, issue the following command:

```bash
sam build --parameter-overrides EndpointName=x ApiKey=y EnterpriseId=z
```

Once built, you can test it locally using the following command

```bash
sam local start-api --parameter-overrides EndpointName=x ApiKey=y EnterpriseId=z
```

With the above command, you will see something like this:

```bash
(esper-sample-solutions) PS C:\repos\esper-sample-solutions\esper-sam-auto-app-updater> sam local start-api --parameter-overrides EndpointName=x ApiKey=y EnterpriseId=z
Mounting EsperSamAutoAppUpdaterFunction at http://127.0.0.1:3000/updateme [POST]
You can now browse to the above endpoints to invoke your functions. You do not need to restart/reload SAM CLI while working on your functions, changes will be reflected instantly/automatically. You only need to restart SAM CLI if you update your AWS SAM template
2020-03-26 20:46:11  * Running on http://127.0.0.1:3000/ (Press CTRL+C to quit)
Invoking app.lambda_handler (python3.7)

Fetching lambci/lambda:python3.7 Docker container image......
Mounting C:\repos\esper-sample-solutions\esper-sam-auto-app-updater\.aws-sam\build\EsperSamAutoAppUpdaterFunction as /var/task:ro,delegated inside runtime container
START RequestId: a2c969ae-bf2f-1453-dd52-b3e7742c8153 Version: $LATEST
```

Now you can test locally as follows:

```bash
curl -s --header "Content-Type: application/json" \
  --request POST \
  --data '{"device_id":"ABC-DEF-GHIJ","pkg":"io.esper.foo","build_number":"99"}' \
  http://127.0.0.1:3000/updateme
```

### Deploy to production

To deploy this to production, issue a command as follows:

```bash
sam deploy --parameter-overrides EndpointName=x ApiKey=y EnterpriseId=z
```

At the end of the command, you will see something like this:

```bash
CloudFormation outputs from deployed stack
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------   
Outputs                                                                                                                                                                                                                                                                                      
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------   
.
.
.
Key                 EsperSamAutoAppUpdaterApi
Description         API Gateway endpoint URL for Prod stage for EsperSamAutoAppUpdater function
Value               https://r89y34l2j4.execute-api.us-west-2.amazonaws.com/Prod/updateme/
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
```

You can now issue commands from the device to the URL listed above (e.g. `https://r89y34l2j4.execute-api.us-west-2.amazonaws.com/Prod/updateme/` in the above case)

```bash
curl -s --header "Content-Type: application/json" \
  --request POST \
  --data '{"device_id":"ABC-DEF-GHIJ","pkg":"io.esper.foo","build_number":"99"}' \
  https://r89y34l2j4.execute-api.us-west-2.amazonaws.com/Prod/updateme/
```

## Usage on the Device

In order to use this mechanism from the device, one would make use of the [Esper Device SDK](https://docs.esper.io/home/devicesdk.html) in their application to [get the device ID](https://docs.esper.io/home/devicesdk.html#getting-device-info). Assuming that the device is provisioned with Esper, when the application is launched the first time after boot, it should call this API to cause Esper to force an app-update on itself, should an update be necessary.

Please ensure you call this API only *once* per boot session. Also, limit the calls to the Lambda as much as possible.

## More Reading

Please see AWS' [Tutorial: Deploying a Hello World Application](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-getting-started-hello-world.html) for more information.