FlowDm public deploy (Railway)

1. Create a GitHub account and a new empty repository named flowdm-public.
2. Upload all files from this archive to that repository.
3. On railway.com: New Project -> Deploy from GitHub Repo -> choose flowdm-public.
4. Railway automatically installs requirements.txt and runs Procfile.
5. In Railway Variables add SECRET_KEY with a long random value.
6. In Settings -> Networking -> Generate Domain. This is your public link.

Important: Railway local disk/database can be reset during redeploys. For a real permanent service, move users/messages to Railway PostgreSQL.
