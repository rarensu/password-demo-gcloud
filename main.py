# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START gae_python38_render_template]
# [START gae_python3_render_template]
import datetime

from flask import Flask, render_template, request, url_for, flash, redirect

app = Flask(__name__)
app.config['SECRET_KEY']='49f8857340c5c962c18790de5f89fe36408a80e6b9f21b06'

import os 
bucket_name=os.environ.get('GOOGLE_CLOUD_PROJECT')+'.appspot.com'

from google.cloud import storage

min_passwd_len=2

import json

import password

def upload_blob_from_memory(bucket_name, contents, destination_blob_name):
    """Uploads a file to the bucket."""

    # The ID of your GCS bucket
    # bucket_name = "your-bucket-name"

    # The contents to upload to the file
    # contents = "these are my contents"

    # The ID of your GCS object
    # destination_blob_name = "storage-object-name"

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_string(contents)

    print(
        f"{destination_blob_name} with contents {contents} uploaded to {bucket_name}."
    )

def download_blob_into_memory(bucket_name, blob_name):
    """Downloads a blob into memory."""
    # The ID of your GCS bucket
    # bucket_name = "your-bucket-name"

    # The ID of your GCS object
    # blob_name = "storage-object-name"

    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)

    # Construct a client side representation of a blob.
    # Note `Bucket.blob` differs from `Bucket.get_blob` as it doesn't retrieve
    # any content from Google Cloud Storage. As we don't need additional data,
    # using `Bucket.blob` is preferred here.
    blob = bucket.blob(blob_name)
    contents = blob.download_as_string()

    print(
        "Downloaded storage object {} from bucket {} as the following string: {}.".format(
            blob_name, bucket_name, contents
        )
    )
    return contents

def delete_blob(bucket_name, blob_name):
    """Deletes a blob from the bucket."""
    # bucket_name = "your-bucket-name"
    # blob_name = "your-object-name"

    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    generation_match_precondition = None

    # Optional: set a generation-match precondition to avoid potential race conditions
    # and data corruptions. The request to delete is aborted if the object's
    # generation number does not match your precondition.
    blob.reload()  # Fetch blob metadata to use in generation_match_precondition.
    generation_match_precondition = blob.generation

    blob.delete(if_generation_match=generation_match_precondition)

    print(f"Blob {blob_name} deleted.")

def list_blobs(bucket_name):
    """Lists all the blobs in the bucket."""
    # bucket_name = "your-bucket-name"

    storage_client = storage.Client()

    # Note: Client.list_blobs requires at least package version 1.17.0.
    blobs = storage_client.list_blobs(bucket_name)

    # Note: The call returns a response only when the iterator is consumed.
    blob_names = [blob.name for blob in blobs]

    for blob_name in blob_names:
        print(blob_name)
    return blob_names

def check_if_blob_name_valid(bucket_name,blob_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    try:
        bucket.blob(blob_name).exists(storage_client)
    except Exception as e:
        print(e)
        return False
    return True

def check_if_blob_exists(bucket_name, blob_name):
    """Check if a specific blob exists in the bucket."""
    # bucket_name = "your-bucket-name"

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    # Note: Client.list_blobs requires at least package version 1.17.0.
    blob = bucket.blob(blob_name)
    return blob.exists(storage_client)

@app.route("/")
def root():
    return render_template("index.html")

@app.route("/users/")
def users():
    usernames = list_blobs(bucket_name)
    return render_template("users.html", usernames=usernames)

@app.route('/create/', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        u = request.form['usernamefield']
        p = request.form['passwordfield']

        if not u:
            flash('Username is required!',"alert")
        elif not check_if_blob_name_valid(bucket_name, u):
            flash('Username "'+u+'" is not valid!',"alert")
        elif check_if_blob_exists(bucket_name, u):
            flash('User "'+u+'" already exists!',"alert")
        elif not p:
            flash('Password is required!',"alert")
        elif len(p) < min_passwd_len:
            flash('Password is too short!',"alert")
        else:
            server_hashes=password.multihash64(p)
            hashtext=json.dumps(server_hashes)
            upload_blob_from_memory(bucket_name, hashtext, u)
            print(u, p)
            flash('User "'+u+'" created.',"yay")
            return redirect(url_for('users'))

    return render_template('create.html')

@app.route('/test/', methods=('GET', 'POST'))
def test():
    if request.method == 'POST':
        u = request.form['usernamefield']
        p = request.form['passwordfield']

        if not u:
            flash('Username is required!',"alert")
        elif not check_if_blob_name_valid(bucket_name, u):
            flash('Username "'+u+'" is not valid!',"alert")
        elif not check_if_blob_exists(bucket_name, u):
            flash('User "'+u+'" does not exist!',"alert")
        elif not p:
            flash('Password is required!',"alert")
        elif len(p) < min_passwd_len:
            flash('Password is too short!',"alert")
        else:
            hashtext=download_blob_into_memory(bucket_name,u)
            server_hashes=json.loads(hashtext)
            client_hashes=password.multihash(p)
            if password.match_count(client_hashes, server_hashes):
                flash('User "'+u+'" Successfully Authenticated!',"yay")
                return render_template('test.html')
            else:
                flash('User "'+u+'" Authentication Failed!',"alert")
            
    return render_template('test.html')

@app.route('/delete/', methods=('GET', 'POST'))
def delete():
    if request.method == 'POST':
        u = request.form['usernamefield']
        p = request.form['passwordfield']

        if not u:
            flash('Username is required!',"alert")
        elif not check_if_blob_name_valid(bucket_name, u):
            flash('Username "'+u+'" is not valid!',"alert")
        elif not check_if_blob_exists(bucket_name, u):
            flash('User "'+u+'" does not exist!',"alert")
        elif not p:
            flash('Password is required!',"alert")
        elif len(p) < min_passwd_len:
            flash('Password is too short!',"alert")
        else:
            hashtext=download_blob_into_memory(bucket_name,u)
            server_hashes=json.loads(hashtext)
            client_hashes=password.multihash(p)
            if password.match_count(client_hashes, server_hashes):
                delete_blob(bucket_name, u)
                flash('User "'+u+'" Deleted!',"yay")
                return redirect(url_for('users'))
            else:
                flash('User "'+u+'" Authentication Failed!',"alert")

    return render_template('delete.html')

@app.route('/expose/', methods=('GET', 'POST'))
def expose():
    if request.method == 'POST':
        u = request.form['usernamefield']
        v = 'villainy' in request.form.keys()
        if not v:
            flash('Pledge is required!',"alert")
        elif not u:
            flash('Username is required!',"alert")
        elif not check_if_blob_name_valid(bucket_name, u):
            flash('Username "'+u+'" is not valid!',"alert")
        elif not check_if_blob_exists(bucket_name, u):
            flash('User "'+u+'" does not exists!',"alert")
        else:
            hashtext=download_blob_into_memory(bucket_name,u)
            #server_hashes=json.loads(hashtext)
            flash('User "'+u+'" exposed.',"yay")
            return render_template('expose.html', hashtext=hashtext)

    return render_template('expose.html',hashtext=None)

if __name__ == "__main__":
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host="127.0.0.1", port=8080, debug=True)
# [END gae_python3_render_template]
# [END gae_python38_render_template]
