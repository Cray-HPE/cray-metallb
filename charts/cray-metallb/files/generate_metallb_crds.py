import yaml
import argparse
import os

def generate_metallb_crds(customizations_yaml_path):
    crd_yamls = []
    with open(customizations_yaml_path, 'r') as customizations_file:
        customizations = yaml.safe_load(customizations_file)
    bgp_peers = customizations['spec']['network']['metallb']['peers']
    address_pools = customizations['spec']['network']['metallb']['address-pools']

    unknown_peer_counter = 1

    # 1. Generate BGPPeer CRDs
    for peer in bgp_peers:
        peer_ip = peer['peer-address']
        
        actual_device_network = peer.get('device-network')
        # Determine the effective network part for naming and for grouping in BGPAdvertisements
        # If device-network is missing, assume 'nmn'
        effective_network_part = actual_device_network if actual_device_network is not None else 'nmn'
        peer['effective_network_for_grouping'] = effective_network_part

        device_name_val = peer.get('device-name')
        final_peer_name_for_crd = ""

        if device_name_val is not None:
            # device-name is present, form name like "device-name-EFFECTIVE_NETWORK"
            final_peer_name_for_crd = f"{device_name_val}-{effective_network_part}"
        else:
            # device-name is missing, use "unknown-peerX"
            # This handles the case where "device-name and device-network fields are not present"
            # by defaulting to unknown-peerX if device-name is missing.
            final_peer_name_for_crd = f"unknown-peer{unknown_peer_counter}"
            unknown_peer_counter += 1
        
        peer['generated_crd_name'] = final_peer_name_for_crd

        bgp_peer_crd = {
            'apiVersion': 'metallb.io/v1beta2',
            'kind': 'BGPPeer',
            'metadata': {
                'name': final_peer_name_for_crd,
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
    nmn_peer_names = []
    cmn_peer_names = []
    chn_peer_names = []

    for peer in bgp_peers:
        peer_name_for_advertisement = peer['generated_crd_name']
        effective_device_network = peer['effective_network_for_grouping']
        
        if effective_device_network == 'nmn':
            nmn_peer_names.append(peer_name_for_advertisement)
        elif effective_device_network == 'cmn':
            cmn_peer_names.append(peer_name_for_advertisement)
        elif effective_device_network == 'chn':
            chn_peer_names.append(peer_name_for_advertisement)
    
    if nmn_peer_names:
        bgp_adv_node_mgmt = {
            'apiVersion': 'metallb.io/v1beta1',
            'kind': 'BGPAdvertisement',
            'metadata': {
                'name': 'node-management',
                'namespace': 'metallb-system'
            },
            'spec': {
                'ipAddressPools': ['node-management', 'hardware-management'],
                'peers': nmn_peer_names
            }
        }
        crd_yamls.append(yaml.dump(bgp_adv_node_mgmt))

    cmn_networks = ['customer-management-static', 'customer-management']
    if chn_peer_names:
        bgp_adv_customer_high_speed = {
            'apiVersion': 'metallb.io/v1beta1',
            'kind': 'BGPAdvertisement',
            'metadata': {
                'name': 'customer-high-speed',
                'namespace': 'metallb-system'
            },
            'spec': {
                'ipAddressPools': ['customer-high-speed'],
                'peers': chn_peer_names
            }
        }
        crd_yamls.append(yaml.dump(bgp_adv_customer_high_speed))
    else:
        cmn_networks.append('customer-access')

    if cmn_peer_names:
        bgp_adv_customer_mgmt = {
            'apiVersion': 'metallb.io/v1beta1',
            'kind': 'BGPAdvertisement',
            'metadata': {
                'name': 'customer-management',
                'namespace': 'metallb-system'
            },
            'spec': {
                'ipAddressPools': cmn_networks,
                'peers': cmn_peer_names
            }
        }
        crd_yamls.append(yaml.dump(bgp_adv_customer_mgmt))

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
