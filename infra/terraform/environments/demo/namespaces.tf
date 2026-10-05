# Matches the HLD's three namespaces exactly: ueransim, open5gs, aegis.
# Phase 2 installs the actual Helm charts into these.
resource "kubernetes_namespace_v1" "ueransim" {
  metadata {
    name = "ueransim"
  }
  depends_on = [module.eks]
}

resource "kubernetes_namespace_v1" "open5gs" {
  metadata {
    name = "open5gs"
  }
  depends_on = [module.eks]
}

resource "kubernetes_namespace_v1" "aegis" {
  metadata {
    name = "aegis"
  }
  depends_on = [module.eks]
}
