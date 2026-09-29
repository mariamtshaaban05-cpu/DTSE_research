import pandas as pd
import os
from table_pypsa.run_pypsa import build_network, run_pypsa
from table_pypsa.utilities.load_costs import load_costs
import argparse
import copy
import pickle

# Get file name from command line argument
parser = argparse.ArgumentParser()
parser.add_argument('--file_name', '-f', help='Name of the base case file', required=True)
parser.add_argument('--tech_name', '-t', help='Name of the component to be scanned', required=True)
parser.add_argument('--cost_factors', '-c', help='Values of component attribute to be scanned', required=True)
parser.add_argument('--elec_cost', '-e', help='Set if electricity cost should be scanned', action='store_true')
parser.add_argument('--component', '-p', help='Component to be cost scanned if not all together', default='all')

def replace_electricity_costs(cost_factor, scan_tech, tech_comp, n):
    """
    Replace electricity costs time series of the buyer/seller to market with time series 
    obtained from optimization without underground thermal storage.
    """
    # Read electricity costs time series from optimization without underground thermal storage
    res_path = 'output_data/btes_base_case_orca_no_btes/btes_output_no_btes_{0}_costsx{1}.pickle'.format(scan_tech, str(cost_factor).replace('.','p'))
    with open(res_path, 'rb') as f:
        data = pickle.load(f)

        time_data = data['time results']
        electricity_costs = time_data[['electricity marginal cost']]
        n.snapshots = electricity_costs.index
        if tech_comp == 'const_generator':
            n.generators_t['marginal_cost'][tech_comp] = electricity_costs
        elif tech_comp == 'power_seller':
            n.links_t['marginal_cost'][tech_comp] = -1*electricity_costs
        else:
            raise ValueError('Invalid tech_comp value: {0}'.format(tech_comp))
        f.close()
    return n

def scan_costs(base_case_file, cost_factors, tech_name, component, elec_cost=False):
    """
    Scan costs of a specific technology in the network.
    """

    network, case_dict, component_list, comp_attributes = build_network(base_case_file)
    base_costs = pd.read_csv(case_dict['costs_path'],index_col=[0, 1]).sort_index()


    for cost_factor in cost_factors:
        # Create deep copies of network and component_list
        network_copy = copy.deepcopy(network)
        component_list_copy = copy.deepcopy(component_list)

        if elec_cost:
            tech_names = ['const_generator', 'power_seller']
        
        else:
            if tech_name == "fossil":
                tech_names = ['natgas', 'oil']
            elif tech_name == "wind_solar":
                tech_names = ['wind', 'solar']
            else:
                tech_names = [tech_name]

        for technology in tech_names:
            if not cost_factor == 1 and not technology == "nothing":
                # Run over all components that have tech_name in their name
                if component == 'all':
                    run_techs = [comp['name'] for comp in component_list_copy if technology in comp['carrier']]
                else:
                    run_techs = [comp['name'] for comp in component_list_copy if technology in comp['carrier'] and comp['name']==component]
                # Get the technology name from the component list
                for tech_component in run_techs:
                    for cost_parameter in ['capital_cost', 'marginal_cost']:

                        component_type = [getattr(network_copy, comp_type) for comp_type in ['links', 'generators', 'stores'] if tech_component in getattr(network_copy, comp_type).index][0]
                        print('Old {0} for {1}: {2}'.format(cost_parameter, tech_component, component_type.loc[tech_component, cost_parameter]))
                        
                        if elec_cost:
                            if cost_parameter == 'capital_cost':
                                continue
                            network_copy = replace_electricity_costs(cost_factor, tech_name, technology, network_copy)
                        
                        else:
                            component_type.loc[tech_component, cost_parameter] = cost_factor * component_type.loc[tech_component, cost_parameter]
                        print('New {0} for {1}: {2}'.format(cost_parameter, tech_component, component_type.loc[tech_component, cost_parameter]))
                        # Replace new costs in network_copy and component_list_copy
                        tech_indeces = [i for i in range(len(component_list_copy)) if tech_component in component_list_copy[i]['name']]
                        for tech_index in tech_indeces:
                            component_list_copy[tech_index][cost_parameter] = component_type.loc[tech_component, cost_parameter]
        
        # Run PyPSA with new costs
        comp_label = component if not component=='all' else tech_name
        run_pypsa(network_copy, base_case_file, case_dict, component_list_copy, outfile_suffix='_{0}_costsx{1}'.format(comp_label, str(cost_factor).replace('.', 'p')))

if __name__ == "__main__":
    args = parser.parse_args()
    base_case_file = args.file_name
    cost_factors = list(map(float, args.cost_factors.split(',')))
    tech_name = args.tech_name
    component = args.component
    elec_cost = args.elec_cost

    scan_costs(base_case_file, cost_factors, tech_name, component, elec_cost)