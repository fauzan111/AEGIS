# UERANSIM — Helm

Two separate charts, both from Gradiant, matching the HLD's two boxes ("UE (UERANSIM)" and "UERANSIM gNB" drawn separately).

## Chart coordinates

```
oci://registry-1.docker.io/gradiantcharts/ueransim-gnb  version 0.2.6  (app v3.2.6)
oci://registry-1.docker.io/gradiantcharts/ueransim-ues  version 0.1.2  (app v3.2.6)
```

Both confirmed by actually pulling them — and the versions are genuinely different from each other (0.2.6 vs 0.1.2), not a typo. Worth flagging: these charts haven't had a release since early 2024, unlike Open5GS's chart (three releases in the week this was checked). Functionally UERANSIM itself doesn't change fast, but don't assume parity with whatever UERANSIM version the local Docker Compose testbed used without checking — both pin app version `3.2.6`.

## Install order

The gNB needs the AMF reachable (its `amf.hostname` default points at `open5gs-amf-ngap`, which only exists once Open5GS is installed), and the UE needs the gNB reachable. Install Open5GS first, then gNB, then UE:

```bash
helm install ueransim-gnb oci://registry-1.docker.io/gradiantcharts/ueransim-gnb \
  --version 0.2.6 \
  --namespace ueransim \
  -f values-gnb.yaml

# Same Secret as the Open5GS install — see infra/helm/open5gs/README.md.
# Note: this chart's `initialMSISDN` field actually wants the MSIN (the
# IMSI with mcc+mnc stripped off), not the full IMSI — it builds the
# UE's supi as imsi-{mcc}{mnc}{initialMSISDN}. Passing the full IMSI
# here produces a garbled, non-matching supi. See the comment in
# infra/k8s/subscriber-secret.yaml for how this was caught.
MSIN=$(kubectl -n open5gs get secret aegis-subscriber -o jsonpath='{.data.msin}' | base64 -d)
K=$(kubectl -n open5gs get secret aegis-subscriber -o jsonpath='{.data.k}' | base64 -d)
OP=$(kubectl -n open5gs get secret aegis-subscriber -o jsonpath='{.data.op}' | base64 -d)

helm install ueransim-ues oci://registry-1.docker.io/gradiantcharts/ueransim-ues \
  --version 0.1.2 \
  --namespace ueransim \
  -f values-ues.yaml \
  --set mcc=001 --set mnc=01 \
  --set key="$K" --set op="$OP" --set-string initialMSISDN="$MSIN"
```

`initialMSISDN` specifically needs `--set-string`, not plain `--set`. Helm's own `--set` parser tries to coerce numeric-looking strings into actual numbers, and the chart's schema then rejects that with `got number, want string`. It doesn't bite `mcc`/`mnc`/`op` here: Helm special-cases any leading-zero value (`001`, `01`) to stay a string, and `op` (32 digits) overflows `int64` and falls back to a string too, confirmed by rendering the chart with `--set op="$OP"` and checking the output still shows `op: '111...1'`, not a float. `initialMSISDN` ($MSIN, e.g. `1234567895`) has no leading zero and fits in `int64`, so it's the one value that actually gets silently turned into a number unless forced to stay a string.

## Why `mcc`/`mnc` are overridden to `001`/`01`

Both charts default to UERANSIM's generic test PLMN (`999`/`70`). That's **not** what the existing subscriber actually uses — confirmed directly from the real captured SBI traffic (`reports/GATE-3/real_sbi_capture.csv`), whose UDM query paths carry `plmn-id={"mcc":"001","mnc":"01"}`. Using the chart defaults here would have meant the gNB broadcasts a PLMN the provisioned subscriber doesn't belong to, and the UE would fail to register — caught by checking the real capture, not assumed from the IMSI's leading digits.

## Verify

```bash
kubectl -n ueransim logs deploy/ueransim-gnb
kubectl -n ueransim logs deploy/ueransim-ues   # look for "PDU Session establishment is successful", same check as the local runbook
```
