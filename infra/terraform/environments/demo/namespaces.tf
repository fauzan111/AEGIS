# Matches the HLD's three namespaces exactly: ueransim, open5gs, aegis.
# Phase 2 installs the actual Helm charts into these.
#
# All three are labeled at the `privileged` Pod Security Standard
# (not the default `restricted`/`baseline`), because real workloads
# in each one need it:
#   - open5gs: the UPF container needs `privileged: true` + NET_ADMIN
#     to create its `ogstun` TUN device (confirmed in Gradiant's
#     open5gs-upf chart defaults).
#   - ueransim: the simulated UE needs the same, for its own tunnel
#     interface.
#   - aegis: the SBI capture Job runs tcpdump pinned to the SCP node
#     with host networking, which needs NET_ADMIN/NET_RAW.
# This is a deliberate, visible trade-off for a short-lived demo
# environment, not an oversight — Phase 6's guardrail pass should
# re-confirm nothing beyond these three specific workloads ends up
# relying on it.
locals {
  privileged_namespace_labels = {
    "pod-security.kubernetes.io/enforce" = "privileged"
    "pod-security.kubernetes.io/warn"    = "privileged"
  }
}

resource "kubernetes_namespace_v1" "ueransim" {
  metadata {
    name   = "ueransim"
    labels = local.privileged_namespace_labels
  }
  depends_on = [module.eks]
}

resource "kubernetes_namespace_v1" "open5gs" {
  metadata {
    name   = "open5gs"
    labels = local.privileged_namespace_labels
  }
  depends_on = [module.eks]
}

resource "kubernetes_namespace_v1" "aegis" {
  metadata {
    name   = "aegis"
    labels = local.privileged_namespace_labels
  }
  depends_on = [module.eks]
}
