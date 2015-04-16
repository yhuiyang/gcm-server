#gcm-server

### What's this?
This project implements the **_3rd-party application server_** described in [this document](http://developer.android.com/google/gcm/server.html#doc_col), and can only run on Google AppEngine python2.7 runtime. It supports only JSON format sent by HTTP POST. No plan to implement plain-text format or CCS(XMPP) server which can do upstream communication (device to cloud) as well.

The code is divided into several [modules](https://cloud.google.com/appengine/docs/python/modules/), and briefly described as following:
- default module: serves most static assets used on web pages, ex: *.js, *.css, *.jpg, *.png, *.ico, robots.txt,...etc.
- admin module: processes request from admin web pages.
- api module: processes request from Android devices.
- cron module: executes a few simple statistics.
- taskqueue module: communicates with Google Connection Servers


### How to use this?
Assumes you have already created a project on app engine console, and your application id is `app_id`, then change to the top directory of this project and run below command (single line, no wrap) on your command console: 

`appcfg.py -A app_id --oauth2 update app.yaml module_admin.yaml module_api.yaml module_cron.yaml module_taskqueue.yaml`

