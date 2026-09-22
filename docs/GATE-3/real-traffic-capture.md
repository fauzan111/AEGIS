# Real M2M / API-gateway traffic capture - runbook

Gate 3 deliverable: extend AEGIS's validation from the synthetic generator to
real 5G core signalling, per the plan on Gate 2 slide 17 (Open5GS + UERANSIM +
tcpdump/tshark). This is the exact procedure used to produce
`reports/GATE-3/real_sbi_capture.csv` - re-run it to refresh the sample.

## 1. Stand up the 5G core

Clone `herlesupreeth/docker_open5gs` as a sibling to this repo (kept out of
AEGIS's own git history - it's infrastructure, not project source):

```
cd 5G_Project
git clone --depth 1 https://github.com/herlesupreeth/docker_open5gs.git open5gs-testbed
cd open5gs-testbed
```

Pull the pre-built images rather than building from source:

```
docker pull ghcr.io/herlesupreeth/docker_open5gs:master
docker tag ghcr.io/herlesupreeth/docker_open5gs:master docker_open5gs
docker pull ghcr.io/herlesupreeth/docker_ueransim:master
docker tag ghcr.io/herlesupreeth/docker_ueransim:master docker_ueransim
```

**Windows-specific gotcha:** if you cloned with git's default line-ending
conversion, every shell script in the repo gets CRLF line endings, which
breaks their shebang line (`/bin/bash^M: bad interpreter`) and makes every
container exit immediately with code 126. Fix once, before first boot:

```
find . -name "*.sh" -not -path "./.git/*" -exec sed -i 's/\r$//' {} \;
```

Bring up the core:

```
docker compose -f sa-deploy.yaml up -d
```

All 14 services (nrf, scp, ausf, udr, udm, smf, upf, amf, pcf, bsf, nssf,
webui, metrics, mongo, grafana) should show `Up` in `docker ps`. Confirm real
signalling is already flowing by checking `docker logs amf` for NF
registration/discovery lines.

## 2. Provision a test subscriber

Do this through the webui's own REST API, not a hand-built MongoDB document -
the raw Mongoose schema looks simple, but the C-side UDR/UDM query path is
sensitive to subtleties Mongoose normally handles for you (e.g. a hand-built
document that's schema-correct on paper still made UDR report "No
ProvisionedDataSets" during testing here). Login is session + CSRF protected;
the actual create endpoint takes a JWT bearer token and matches the exact
Mongoose model name (`Subscriber`, not the plural `subscribers` you'd expect
from a typical REST convention):

```bash
# 1. Get a CSRF token + session cookie
curl -s -c cookies.txt http://localhost:9999/api/auth/csrf
# -> {"csrfToken": "..."}

# 2. Log in (needs the CSRF token from step 1 as a header)
curl -s -c cookies.txt -b cookies.txt -X POST http://localhost:9999/api/auth/login \
  -H "Content-Type: application/json" -H "x-csrf-token: <token>" \
  -d '{"username":"admin","password":"1423"}'

# 3. Get a JWT + a fresh CSRF token for the authenticated session
curl -s -c cookies.txt -b cookies.txt http://localhost:9999/api/auth/session
# -> {"authToken": "...", "csrfToken": "...", ...}

# 4. Create the subscriber (note: /api/db/Subscriber, exact model name, singular)
curl -s -c cookies.txt -b cookies.txt -X POST http://localhost:9999/api/db/Subscriber \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <authToken>" -H "x-csrf-token: <fresh csrfToken>" \
  -d '{
    "imsi": "001011234567895", "msisdn": ["9076543210"],
    "security": {"k": "8baf473f2f8fd09487cccbd7097c6862",
                 "op": "11111111111111111111111111111111", "amf": "8000"},
    "ambr": {"downlink": {"value":1,"unit":3}, "uplink": {"value":1,"unit":3}},
    "slice": [{"sst":1, "default_indicator":true, "session":[{
      "name":"internet", "type":1,
      "qos": {"index":9, "arp":{"priority_level":8,"pre_emption_capability":1,"pre_emption_vulnerability":1}},
      "ambr": {"downlink":{"value":1,"unit":3}, "uplink":{"value":1,"unit":3}}
    }]}]
  }'
```

IMSI/K/OP here match the `.env` file's `UE1_*` values, which UERANSIM's UE
config templates from directly - keep them in sync.

## 3. Trigger real registration + a PDU session

```
docker compose -f nr-gnb.yaml up -d && sleep 3
docker compose -f nr-ue.yaml up -d
docker logs nr_ue   # look for "PDU Session establishment is successful"
```

## 4. Capture the SBI traffic

All NFs here talk over indirect communication via the SCP, so the AMF's own
network namespace sees nearly everything interesting for one UE's lifecycle
(auth, subscriber-data fetch, policy association, PDU session create/modify).
Capture on port 7777 (the SBI HTTP/2 port every NF listens on) using a
`netshoot` container sharing AMF's network namespace - no changes to AMF
itself required:

```bash
docker run -d --name capture --network container:amf --cap-add NET_ADMIN \
  -v "$(pwd)/captures:/captures" nicolaka/netshoot \
  tcpdump -i any -w /captures/sbi_capture.pcap "tcp port 7777 or sctp"

docker restart nr_ue   # re-trigger a fresh registration + PDU session while capturing
sleep 8
docker stop capture
```

(On Windows/Git Bash, prefix Docker commands touching container-internal
paths with `MSYS_NO_PATHCONV=1` - otherwise paths like `/captures/...` get
silently rewritten into a Windows path and tcpdump fails with "No such file
or directory".)

## 5. Parse into a labelled CSV

`AEGIS/src/parse_real_sbi_capture.py` pairs each HTTP/2 request with its
response (matched by TCP stream + HTTP/2 stream ID, since HTTP/2 multiplexes
many exchanges per connection), maps the destination NF from the SBI path's
service-name prefix (`nudm-sdm` -> UDM, `nsmf-pdusession` -> SMF, ...), and
writes `caller_nf, callee_nf, method, path, status, resp_size` per exchange.

```bash
# tshark isn't required locally - run it through the same netshoot image and
# pipe the output straight into the parser via stdin ('-' as the pcap arg):
docker run --rm -v "$(pwd)/captures:/captures" nicolaka/netshoot \
  tshark -r /captures/sbi_capture.pcap -d tcp.port==7777,http2 -Y "http2.type==1" \
  -T fields -E separator=";" -E occurrence=f \
  -e frame.time_epoch -e ip.src -e ip.dst -e tcp.stream \
  -e http2.headers.method -e http2.headers.path -e http2.headers.status \
  -e http2.headers.content_length -e http2.streamid \
  | python AEGIS/src/parse_real_sbi_capture.py -
```

Output: `AEGIS/reports/GATE-3/real_sbi_capture.csv`.

## What this validates (and what it doesn't)

**Validates:** AEGIS's synthetic generator's endpoint-naming convention
(`Nxxx-yyy/service` paths, one row per request, NF attribution) matches real
Open5GS traffic almost exactly - `Nudm_SDM/get` in the synthetic generator
and `/nudm-sdm/v2/{imsi}/...` in the real capture are the same 3GPP service,
confirmed independently rather than assumed.

**Does not yet validate:** actual AEGIS detection (rules/ML scoring) against
this real traffic - this capture is a single legitimate UE's registration,
with no attack traffic and no fingerprinting/scoring run against it yet.
Feeding a real trace through the actual `aegis_detect.py` pipeline (not just
comparing schemas) is the natural next step, and would need either a much
longer real capture with organic traffic variety, or synthetic attacks
replayed against this same real core so there's something to detect.
