import yaml
import argparse
import os

def generate_metallb_crds(customizations_yaml_path):
    crd_yamls = []
    with open(customizations_yaml_path, 'r') as customizations_file:
        customizations = yaml.safe_load(customizations_file)
    bgp_peers = customizations['spec']['network']['metallb']['peers']
    address_pools = customizations['spec']['network']['metallb']['address-pools']
    crd_yamls = []

    for peer in bgp_peers:
        peer_ip = peer['peer-address']
        peer_name = peer.get('peer-name')

        if peer_name is None:
            print(f"Warning: Could not determine peer name for IP {peer_ip}.")
            continue

        # 1. Generate BGPPeer CRDs
        bgp_peer_crd = {
            'apiVersion': 'metallb.io/v1beta2',
            'kind': 'BGPPeer',
            'metadata': {
                'name': peer_name,
                'namespace': 'metallb-system'
            },
            'spec': {
                'peerAddress': peer['peer-address'],
                'peerASN': peer['peer-asn'],
                'myASN': peer['my-asn']
            }
        }
        crd_yamls.append(yaml.dump(bgp_peer_crd))

    # 2. Generate IPAddressPool CRDs
    for pool in address_pools:
        ip_address_pool_crd = {
            'apiVersion': 'metallb.io/v1beta1',
            'kind': 'IPAddressPool',
            'metadata': {
                'name': pool['name'],
                'namespace': 'metallb-system'
            },
            'spec': {
                'addresses': pool['addresses']
            }
        }
        crd_yamls.append(yaml.dump(ip_address_pool_crd))

    # 3. Generate BGPAdvertisement CRDs
    nmn_peers = []
    cmn_peers = []
    chn_peers = []

    for peer in bgp_peers:
        peer_name = peer.get('peer-name')
        device_network = peer.get('device-network')
        if device_network == 'nmn':
            nmn_peers.append(peer_name)
        elif device_network == 'cmn':
            cmn_peers.append(peer_name)
        elif device_network == 'chn':
            chn_peers.append(peer_name)
    
    if nmn_peers:
        bgp_adv_node_mgmt = {
            'apiVersion': 'metallb.io/v1beta1',
            'kind': 'BGPAdvertisement',
            'metadata': {
                'name': 'node-management',
                'namespace': 'metallb-system'
            },
            'spec': {
                'ipAddressPools': ['node-management', 'hardware-management'],
                'peers': nmn_peers
            }
        }
        crd_yamls.append(yaml.dump(bgp_adv_node_mgmt))

    if cmn_peers:
        bgp_adv_customer_mgmt = {
            'apiVersion': 'metallb.io/v1beta1',
            'kind': 'BGPAdvertisement',
            'metadata': {
                'name': 'customer-management',
                'namespace': 'metallb-system'
            },
            'spec': {
                'ipAddressPools': ['customer-management-static', 'customer-management'],
                'peers': cmn_peers
            }
        }
        crd_yamls.append(yaml.dump(bgp_adv_customer_mgmt))

    if chn_peers:
        bgp_adv_customer_high_speed = {
            'apiVersion': 'metallb.io/v1beta1',
            'kind': 'BGPAdvertisement',
            'metadata': {
                'name': 'customer-high-speed',
                'namespace': 'metallb-system'
            },
            'spec': {
                'ipAddressPools': ['customer-high-speed'],
                'peers': chn_peers
            }
        }
        crd_yamls.append(yaml.dump(bgp_adv_customer_high_speed))

    return '---\n'.join(crd_yamls)

def main():
    parser = argparse.ArgumentParser(description='Generate MetalLB CRDs from customizations YAML.')
    parser.add_argument('--input', required=True, help='Path to the input customizations.yaml file')
    parser.add_argument('--output', required=True, help='Path to write the generated CRD YAML file')
    args = parser.parse_args()

    try:
        generated_crd_yaml = generate_metallb_crds(args.input)

        with open(args.output, 'w') as outfile:
            outfile.write(generated_crd_yaml)

    except Exception as e:
        print(f"Error generating MetalLB CRDs: {e}")
        exit(1)

if __name__ == '__main__':
    main()
