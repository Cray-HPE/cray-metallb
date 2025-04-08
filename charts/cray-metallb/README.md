MetalLB
-------

MetalLB is a load-balancer implementation for bare metal [Kubernetes][k8s-home]
clusters, using standard routing protocols.


Introduction
------------

This chart bootstraps a [MetalLB][metallb-home] installation on
a [Kubernetes][k8s-home] cluster using the [Helm][helm-home] package manager.
This chart provides an implementation for LoadBalancer Service objects.

MetalLB is a cluster service, and as such can only be deployed as a
cluster singleton. Running multiple installations of MetalLB in a
single cluster is not supported.

Prerequisites
-------------

-  Kubernetes 1.25+

Installing the Chart
--------------------

The chart can be installed as follows:

```console
$ helm package .
$ helm install -n metallb-system ./<generated-tar> -f values.yaml
```

The command deploys MetalLB on the Kubernetes cluster. This chart will
generate MetalLB CRs with values provided in the `customizations.yaml`
file stored in loftsman. 

Here are the rules for how the advertisements are generated based
on the name of the bgp-peer:
- If the name ends in -nmn, add it to the node-management advertisement
- If the name ends in -cmn, add it to the customer-management advertisement
- If the name starts with sw-edge add it to the customer-high-speed advertisement
 
And then the address pools associated would be:
- node-management advertisement
  - node management pool (NMN)
  - hardware management pool (NMN)
- customer-management advertisement
  - customer management static pool (CMN)
  - customer management pool (CMN)
- customer-high-speed advertisement
  - customer high speed pool (CHN)

Uninstalling the Chart
----------------------

To uninstall/delete the `metallb` deployment:

```console
$ helm delete metallb
```

The command removes all the Kubernetes components associated with the
chart, but will not remove the release metadata from `helm` — this will prevent
you, for example, if you later try to create a release also named `metallb`). To
fully delete the release and release history, simply [include the `--purge`
flag][helm-usage]:

```console
$ helm delete --purge metallb
```

Configuration
-------------

See `values.yaml` for configuration notes. Specify each parameter
using the `--set key=value[,key=value]` argument to `helm
install`. For example,

```console
$ helm install --name metallb \
  --set rbac.create=false \
    stable/metallb
```

The above command disables the use of RBAC rules.

Alternatively, a YAML file that specifies the values for the above
parameters can be provided while installing the chart. For example,

```console
$ helm install --name metallb -f values.yaml stable/metallb
```

By default, this chart generates CRDs for MetalLB based on data
stored in `configurations.yaml` from loftsman.

**Please note:** MetalLB no longer accepts a ConfigMap and must be configured
via CRDs.

[helm-home]: https://helm.sh
[helm-usage]: https://docs.helm.sh/using_helm/
[k8s-home]: https://kubernetes.io
[metallb-arpndp-concepts]: https://metallb.universe.tf/concepts/arp-ndp/
[metallb-config]: https://metallb.universe.tf/configuration/
[metallb-home]: https://metallb.universe.tf
