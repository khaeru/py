import json
import os

from disqusapi import DisqusAPI, Paginator

disqus = DisqusAPI(secret_key="KEY_HERE", public_key="KEY_HERE")

p = Paginator(
    disqus.api,
    "users.listPosts",
    user="username:khaeru",
    limit="100",
    order="asc",
    method="GET",
)

for post in p:
    try:
        filename = "comments/{0[createdAt]}_{0[id]}.json".format(post)
        with open(filename, "x") as f:
            json.dump(post, f)
    except FileExistsError:
        continue

for f in os.listdir("comments"):
    # Further processing…
    pass
