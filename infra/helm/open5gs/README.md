# Open5GS — Helm

Uses Gradiant's maintained chart, not a custom one — confirmed current and actively maintained (three releases in the week this was checked) before writing anything here.

## Chart coordinates

```
oci://registry-1.docker.io/gradiantcharts/open5gs
version 2.3.8 (app version 2.7.5)
```

**Note the registry path is `gradiantcharts`, not `gradiant`** — Artifact Hub's own page for this chart spells out `oci://registry-1.docker.io/gradiantcharts/open5gs` in its install box; `gradiant/open5gs` (what most blog posts and even some of the chart family's own docs pages use) does not resolve. Confirmed by actually pulling it:

```bash
helm pull oci://registry-1.docker.io/gradiantcharts/open5gs --version 2.3.8
```

The chart is distributed over OCI, not a classic `index.yaml` repo — there's no `helm repo add` step.

## What `values.yaml` in this directory changes

The chart's own default enables both 4G/EPC (hss, mme, pcrf, sgwc, sgwu) and 5G/NGC components. Disabled all the 4G ones plus `sepp` (inter-PLMN roaming) — this deployment is 5G SA only, matching the HLD and the existing local Docker Compose testbed exactly.

Confirmed directly from the pulled chart (not from Artifact Hub's cached values table, which was showing a stale old version's defaults — `scp.enabled: false` there, `true` in the chart that's actually tagged 2.3.8): the real current `values.yaml` defaults everything to `true`. Checked `Chart.yaml` too — the per-NF image tags come from each NF's own subchart (`charts/open5gs-amf/`, etc. inside the pulled `.tgz`), not the umbrella's own values, so nothing here pins image versions beyond what the chart itself ships.

**MongoDB dependency:** `mongodb.enabled: true` (chart default, left alone) needs a PersistentVolumeClaim. That needs the EBS CSI driver addon + the `gp3` default StorageClass from `infra/terraform/environments/demo/ebs-csi.tf` — without those, the Mongo pod sits `Pending` forever. Apply the Terraform before installing this chart.

**UPF needs `privileged: true` + `NET_ADMIN`** (confirmed directly in `charts/open5gs-upf/values.yaml` inside the pulled chart) to create its `ogstun` TUN device. This is why the `open5gs` namespace in `infra/terraform/environments/demo/namespaces.tf` is labeled at the `privileged` Pod Security Standard, not the default `restricted`.

## Subscriber provisioning

`populate.initCommands` is left empty in `values.yaml` on purpose — the actual IMSI/K/OP come from the Kubernetes Secret at `infra/k8s/subscriber-secret.yaml`, not committed in plain text here. At install time:

```bash
kubectl apply -f ../../k8s/subscriber-secret.yaml

IMSI=$(kubectl -n open5gs get secret aegis-subscriber -o jsonpath='{.data.imsi}' | base64 -d)
K=$(kubectl -n open5gs get secret aegis-subscriber -o jsonpath='{.data.k}' | base64 -d)
OP=$(kubectl -n open5gs get secret aegis-subscriber -o jsonpath='{.data.op}' | base64 -d)

helm install open5gs oci://registry-1.docker.io/gradiantcharts/open5gs \
  --version 2.3.8 \
  --namespace open5gs \
  -f values.yaml \
  --set-json "populate.initCommands=[\"open5gs-dbctl add $IMSI $K $OP\"]"
```

Worth being honest about: the IMSI/K/OP values in that Secret are the exact same synthetic test vectors already used in the local Docker Compose setup (`docs/GATE-3/real-traffic-capture.md`), kept for consistency. They're not secret in the "this would be bad if leaked" sense — the real value of routing them through a Secret instead of a plain `values.yaml` field is the pattern itself (config indirection), which matters more the day these ever get swapped for something that does need to stay private.

## Verify

```bash
kubectl -n open5gs get pods
kubectl -n open5gs logs deploy/open5gs-amf   # look for NF registration/discovery lines, same check as the local runbook
```
