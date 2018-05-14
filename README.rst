Chunkey
=========

HTTP Live Stream Encoder for endpoints in AWS EC2
--------------------------------------------------

This is a quick HLS library/crawler for conversion from static file
hosting to an HLS solution for quick and high-quality/low-latency
streaming that is adaptible for differing global connection speeds.


|Build|

| [v1.2.3] 2018.5
| (c)(GNU-GPL) @yro 2016

Install
-------

::

    `python setup.py install`

| **NOTE:** This requires a compiled version of ffmpeg (with libx264)
  available here:
| https://trac.ffmpeg.org/wiki/CompilationGuide


Setup
-----

| The “Deliver Root” is optional, and can point to a root subdirectory 
  in the bucket, if desired.  
| The 'encode\_profiles.json' file can act as a template for a set of 
  encoding profiles as desired

Use:
----

::

    from chunkey import Chunkey

    VidChunk = Chunkey(mezz_file = 'link_to/file/to_be/transcoded.mp4')

will generate an HLS manifest with as many streams as indicated by 
default (5), or the optional 'encode\_profiles.json' file pointed to by 
a keyword arg (see below)


Args:
-----

*Mandatory:*

::

    mezz_file = link_to/file/to_be/transcoded.mp4' ##MANDATORY
        can be filepath or URL

*Optional* (will deliver file to endpoint)

*[MUST PASS CREDENTIALS]*

::

    manifest = 'target_manifest_name'

    encode_profiles = 'path/to/encode_profiles.json' ## will read defaults


Credential Passing (optional, for delivery)
----

::

    DELIVER_BUCKET = 's3_bucket_to_deliver_to'

    DELIVER_ROOT = 'optional_bucket_directory'

    ACCESS_KEY_ID = '' 
    
    SECRET_ACCESS_KEY = ''




Retrieve data:
-----
::

    VidChunk.complete -- boolean for completed encode

    VidChunk.manifest_url -- endpoint url for manifest (aws s3) or local dir path

.. |Build| image:: https://travis-ci.org/yro/vhls.svg?branch=master