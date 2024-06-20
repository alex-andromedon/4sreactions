import pickle
import yaml
import os
import tkinter as tk
import datetime
from tkinter import ttk
import xml.etree.ElementTree as ET
import requests
import math
_1dqid = 1030049082711
_jitaid = 60003760
MOON_MATERIALS_GROUP_ID = 427
INTERMEDIATES_GROUP_ID = 428
COMPOSITE_GROUP_ID = 429
FUEL_GROUP_ID = 1136
COMPOSITE_FORMULA_GROUP_ID = 1888
import_cost = 850
export_cost = 850
collateral_rate = 0.005
lang = 'en'
moongoos = {}
formulas = {}
fuels = {}
typeIDs = {}
groups = {}
blueprints = {}
typenames = {}
class Formula:
	def __init__(self, type_id, name):
		self.type_id=type_id
		self.name=name
		self.inputs = {}
		self.product = None

class Fuel:
	def get_tier(self):
		return 4
	def get_all_inputs(self):
		return {}
	def get_cost(self, materials):
		if self.type_id in materials[3] and materials[3][self.type_id] > 100:
			return 0
		return min(self.sell_jita, self.sell_1dq)
	def __init__(self, type_id, name):
		self.type_id=type_id
		self.name=name
		self.cost=-1
		self.products = {}
		self.buy_1dq = -1
		self.buy_jita = -1
		self.sell_jita = -1
		self.sell_1dq = -1
		self.volume = typeIDs[type_id]['volume']
class Moongoo:
	def get_all_inputs(self):
		if self.get_tier() == 1:
			return {}
		all_inputs = {}
		for inp, quantity in self.inputs.items():
			if inp in all_inputs:
				all_inputs[inp] += quantity
			else:
				all_inputs[inp] = quantity
			sub_inputs = inp.get_all_inputs()
			for sub_inp, sub_quantity in sub_inputs.items():
				if sub_inp in all_inputs:
					all_inputs[sub_inp] += sub_quantity
				else:
					all_inputs[sub_inp] = sub_quantity
		return all_inputs
	def get_cost(self, materials):
		if self.get_tier() == 1:
			if self.type_id in materials[0] and materials[0][self.type_id] > 100:
				return 0
			return min(self.sell_jita, self.sell_1dq)
		elif self.get_tier() == 2:
			if self.type_id in materials[1] and materials[1][self.type_id] > 100:
				return 0
			cost = 0
			for inp in self.inputs:
				if isinstance(inp, Fuel):
					cost += inp.get_cost(materials)*5
				else:
					cost += inp.get_cost(materials)*100
			return cost/2
		else:
			cost = 0
			for inp in self.inputs:
				if isinstance(inp, Fuel):
					cost += inp.get_cost(materials)*5
				else:
					cost += inp.get_cost(materials)
			return cost
	def __init__(self, group_id=-1, type_id=-1, name='', inputs=None, products=None, profit=-1000000000000, max_profit_id=-1):
		self.group_id = group_id
		self.type_id = type_id
		self.name = name
		self.profit = profit
		self.max_profit_id = max_profit_id
		self.inputs = inputs if inputs is not None else {}
		self.products = products if products is not None else {}
		self.buy_1dq = -1
		self.buy_jita = -1
		self.sell_jita = -1
		self.sell_1dq = -1
		self.volume = typeIDs[type_id]['volume']
	def get_max_profit(self):
		if self.get_tier() == 3:
			self.max_profit_id = self
			return self.profit
		max_profit = -1
		if len(self.products) > 0:
			for p in self.products:
				if p.get_max_profit() > max_profit:
					max_profit = p.get_max_profit()
					self.profit = max_profit
					self.max_profit_id = p.max_profit_id
		return max_profit
	def get_tier(self):
		return self.group_id-426
def import_typeIDs(yamlpath):
	global typeIDs
	# Load YAML data from the given path
	with open(yamlpath, 'r', encoding='utf-8') as file:
		typeIDs = yaml.safe_load(file)
	# Serialize and save the data to 'typeIDs.pkl'
	with open('typeIDs.pkl', 'wb') as file:
		pickle.dump(typeIDs, file)
	print("typeIDs data serialized and saved to typeIDs.pkl")

def import_groupIDs(grouppath):
	global groups
	with open(grouppath, 'r', encoding='utf-8') as file:
		groups = yaml.safe_load(file)
	with open('groupIDs.pkl', 'wb') as file:
		pickle.dump(groups, file)
	print("groupIDs data serialized and saved to groupIDs.pkl")

def import_blueprints(blueprintspath):
	global blueprints
	# Load YAML data from the given path
	with open(blueprintspath, 'r', encoding='utf-8') as file:
		blueprints = yaml.safe_load(file)
	# Serialize and save the data to 'blueprints.pkl'
	with open('blueprints.pkl', 'wb') as file:
		pickle.dump(blueprints, file)
	print("blueprints data serialized and saved to blueprints.pkl")
def get_reaction_count(item, quant):
	if isinstance(item, Fuel):
		return 5
	return 100
def load_or_import_data(typeIDs_path, blueprints_path, groupIDs_path):
	global typeIDs, blueprints, groups

	# Check if 'typeIDs.pkl' exists
	if os.path.exists('typeIDs.pkl'):
		# Load serialized data
		with open('typeIDs.pkl', 'rb') as file:
			typeIDs = pickle.load(file)
		print("typeIDs data loaded from typeIDs.pkl")
	else:
		# Import data from YAML and serialize it
		import_typeIDs(typeIDs_path)

	# Check if 'blueprints.pkl' exists
	if os.path.exists('blueprints.pkl'):
		# Load serialized data
		with open('blueprints.pkl', 'rb') as file:
			blueprints = pickle.load(file)
		print("blueprints data loaded from blueprints.pkl")
	else:
		# Import data from YAML and serialize it
		import_blueprints(blueprints_path)

	# Check if 'groupIDs.pkl' exists
	if os.path.exists('groupIDs.pkl'):
		# Load serialized data
		with open('groupIDs.pkl', 'rb') as file:
			groups = pickle.load(file)
		print("groupIDs data loaded from groupIDs.pkl")
	else:
		# Import data from YAML and serialize it
		import_groupIDs(groupIDs_path)
def get_type(tid):
	if tid in formulas:
		return Formula
	if tid in fuels:
		return Fuel
	if tid in moongoos:
		return Moongoo
def load_types():
	global moongoos, fuels, formulas
	for tid in typeIDs:
		if typeIDs[tid]['groupID'] in [MOON_MATERIALS_GROUP_ID,INTERMEDIATES_GROUP_ID,COMPOSITE_GROUP_ID]:
			moongoos[tid] = Moongoo(typeIDs[tid]['groupID'], tid, typeIDs[tid]['name'][lang])
		elif typeIDs[tid]['groupID'] == FUEL_GROUP_ID:
			fuels[tid] = Fuel(tid, typeIDs[tid]['name'][lang])
		elif typeIDs[tid]['groupID'] == COMPOSITE_FORMULA_GROUP_ID and tid != 45732: #NO TEST!
			formulas[tid] = Formula(tid, typeIDs[tid]['name'][lang])
	for tid in formulas:
		p = blueprints[tid]['activities']['reaction']['products'][0]
		i = blueprints[tid]['activities']['reaction']['materials']
		moongoos[p['typeID']].formula = formulas[tid]
		formulas[tid].quantity = p['quantity']
		for mat in i:
			t = get_type(mat['typeID'])
			if t is Fuel:
				fuels[mat['typeID']].products[moongoos[p['typeID']]] = p['quantity']
				formulas[tid].inputs[fuels[mat['typeID']]] = mat['quantity']
				moongoos[p['typeID']].inputs[fuels[mat['typeID']]] = mat['quantity']
			elif t is Moongoo:
				moongoos[mat['typeID']].products[moongoos[p['typeID']]] = p['quantity']
				formulas[tid].inputs[moongoos[mat['typeID']]] = mat['quantity']
				moongoos[p['typeID']].inputs[moongoos[mat['typeID']]] = mat['quantity']
	for tid in moongoos:
		typenames[moongoos[tid].name] = tid
	for tid in fuels:
		typenames[fuels[tid].name] = tid
def get_prices():
	global moongoos, fuels
	ids = []
	for goo in moongoos:
		if moongoos[goo].get_tier() != 2:
			ids.append(str(goo))
	for block in fuels:
		ids.append(str(block))
	id_string = ",".join(ids)
	api_string_1dq1 = f'https://goonmetrics.apps.gnf.lt/api/price_data/?station_id={_1dqid}&type_id={id_string}'
	api_string_jita = f'https://goonmetrics.apps.gnf.lt/api/price_data/?station_id={_jitaid}&type_id={id_string}'
	response_1dq1=None
	response_jita=None
	try:
		response_1dq1 = requests.get(api_string_1dq1)
		response_1dq1.raise_for_status()
		root = ET.fromstring(response_1dq1.text)
		for item in root[0]:
			id = int(item.attrib["id"])
			sellprice = float(item.find('sell').find('min').text)
			buyprice = float(item.find('buy').find('max').text)
			if id in fuels:
				fuels[id].sell_1dq = sellprice
				fuels[id].buy_1dq = buyprice
			elif id in moongoos:
				moongoos[id].sell_1dq = sellprice
				moongoos[id].buy_1dq = buyprice
	except requests.exceptions.RequestException as e:
		print(f"Error fetching data from 1DQ1: {e}")
	try:
		response_jita = requests.get(api_string_jita)
		response_jita.raise_for_status()
		root = ET.fromstring(response_jita.text)
		for item in root[0]:
			id = int(item.attrib["id"])
			sellprice = float(item.find('sell').find('min').text)
			buyprice = float(item.find('buy').find('max').text)
			collateralprice = sellprice * collateral_rate
			if id in fuels:
				fuels[id].sell_jita = sellprice + fuels[id].volume * import_cost + collateralprice
				fuels[id].buy_jita = buyprice + fuels[id].volume * export_cost + collateralprice
			elif id in moongoos:
				moongoos[id].sell_jita = sellprice + moongoos[id].volume * export_cost + collateralprice
				moongoos[id].buy_jita = buyprice + moongoos[id].volume * export_cost + collateralprice
	except requests.exceptions.RequestException as e:
		print(f"Error fetching data from Jita: {e}")
def get_profits(materials=[{},{},{},{}]):
	global moongoos
	mp = -1
	mpid = -1
	for gooid in moongoos:
		goo = moongoos[gooid]
		if goo.get_tier() == 3:
			cost = goo.get_cost(materials)
			price = max(goo.buy_1dq, goo.buy_jita) * goo.formula.quantity
			goo.profit = price-cost
	for goo in materials[0]:
		p = goo.get_max_profit()
		if (p > mp or materials[0][goo] < materials[0][mpid]) and materials[0][goo] > 100:
			mp = p
			mpid = goo
	for goo in materials[1]:
		p = goo.get_max_profit()
		if (p > mp or materials[1][goo] < materials[mpid.get_tier()-1][mpid]) and materials[1][goo] > 100:
			mp = p
			mpid = goo
	return mpid

def parse_item(item):
	strarr = item.split('\t')
	if strarr[0] in typenames:
		num = strarr[1].replace(',', '')
		strarr[1] = num
		if num.isnumeric():
			return '\t'.join(strarr[0:2])
	return -1
batches = {}

def ui():
	global batches
	def update_output_reactions():
		global batches
		batchname = batch_name.get("1.0", tk.END).strip()
		if batchname == '':
			batchname = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		if batchname in batches:
			return
		input_text_data = input_text.get("1.0", tk.END).strip().split("\n")
		materials = [{}, {}, {}, {}]
		for item in input_text_data:
			parsed_item = parse_item(item)
			if parsed_item != -1:
				item_name, item_quantity = parsed_item.split('\t')
				item_quantity = int(item_quantity)
				for goo in moongoos.values():
					if goo.name == item_name:
						if goo in materials[goo.get_tier() - 1]:
							materials[goo.get_tier() - 1][goo] += item_quantity
						else:
							materials[goo.get_tier() - 1][goo] = item_quantity
						break
				for fuel in fuels.values():
					if fuel.name == item_name:
						if fuel in materials[3]:
							materials[3][fuel] += item_quantity
						else:
							materials[3][fuel] = item_quantity
						break
		batches[batchname] = {
			'1dqbuy': {},
			'1dqsell': {},
			'jitabuy': {},
			'jitasell': {},
			'reactions': {}
		}
		output_text.configure(state='normal')
		output_text.delete("1.0", tk.END)
		for materialcat in materials:
			for mat in materialcat:
				output_text.insert(tk.END, f'{mat.name} x{materialcat[mat]}\n')
		while True:
			breakout = True
			for mat in materials[0]:
				if materials[0][mat] > get_reaction_count(mat, 1):
					breakout = False
			for mat in materials[1]:
				if materials[1][mat] > get_reaction_count(mat, 1):
					breakout = False
			if breakout:
				break

			max_profit_mat = get_profits(materials)
			reaction_count = materials[max_profit_mat.get_tier() - 1][max_profit_mat]//100
			max_profit_item = max_profit_mat.max_profit_id
			market = '1dqsell' if max_profit_item.buy_1dq > max_profit_item.buy_jita else 'jitasell'
			if max_profit_item in batches[batchname][market]:
				batches[batchname][market][max_profit_item] += reaction_count * max_profit_item.formula.quantity
			else:
				batches[batchname][market][max_profit_item] = reaction_count * max_profit_item.formula.quantity
			
			if max_profit_item in batches[batchname]['reactions']:
				batches[batchname]['reactions'][max_profit_item] += reaction_count
			else:
				batches[batchname]['reactions'][max_profit_item] = reaction_count

			inputs = {}
			for inp in max_profit_item.inputs:
				if inp in materials[1] and materials[1][inp] > reaction_count * get_reaction_count(inp, reaction_count):
					if inp in inputs:
						inputs[inp] += reaction_count * get_reaction_count(inp, reaction_count)
					else:
						inputs[inp] = reaction_count * get_reaction_count(inp, reaction_count)	
				elif isinstance(inp, Fuel):
					if inp in inputs:
						inputs[inp] += reaction_count * get_reaction_count(inp, reaction_count)
					else:
						inputs[inp] = reaction_count * get_reaction_count(inp, reaction_count)
				else:
					for subinp in inp.inputs:
						if inp in batches[batchname]['reactions']:
							batches[batchname]['reactions'][inp] += reaction_count
						else:
							batches[batchname]['reactions'][inp] = reaction_count
						if subinp in inputs:
							inputs[subinp] += reaction_count * get_reaction_count(subinp, reaction_count)
						else:
							inputs[subinp] = reaction_count * get_reaction_count(subinp, reaction_count)


			for inp, quant in inputs.items():
				if inp in materials[inp.get_tier()-1] and materials[inp.get_tier()-1][inp] > get_reaction_count(inp, reaction_count):
					if materials[inp.get_tier()-1][inp] > reaction_count * get_reaction_count(inp, reaction_count):
						materials[inp.get_tier()-1][inp] -= reaction_count * get_reaction_count(inp, reaction_count)
					else:
						if inp.sell_1dq < inp.sell_jita:
							if inp in batches[batchname]['1dqbuy']:
								batches[batchname]['1dqbuy'][inp] += reaction_count * get_reaction_count(inp, reaction_count) - materials[inp.get_tier()-1][inp]
							else:
								batches[batchname]['1dqbuy'][inp] = reaction_count * get_reaction_count(inp, reaction_count) - materials[inp.get_tier()-1][inp]
						else:
							if inp in batches[batchname]['1dqbuy']:
								batches[batchname]['jitabuy'][inp] += reaction_count * get_reaction_count(inp, reaction_count) - materials[inp.get_tier()-1][inp]
							else:
								batches[batchname]['jitabuy'][inp] = reaction_count * get_reaction_count(inp, reaction_count) - materials[inp.get_tier()-1][inp]
						materials[inp.get_tier()-1][inp] = 0
		
		update_batches()



	def update_batches():
		global batches
		
		# Update dropdown values
		batch_options = list(batches.keys()) if batches else ['No batches']
		batch_dropdown['values'] = batch_options
		
		# Set default value
		if batch_options:
			selected_batch.set(batch_options[0])
		else:
			selected_batch.set('No batches')
		
		# Update fields with the first batch
		update_fields()
	def update_fields(event=None):
		selected = selected_batch.get()
		if selected in batches:
			buy_1dq_orders = batches[selected]['1dqbuy']
			buy_jita_orders = batches[selected]['jitabuy']
			sell_1dq_orders = batches[selected]['1dqsell']
			sell_jita_orders = batches[selected]['jitasell']
			reactions = batches[selected]['reactions']

			# Enable the Text widgets to update their content
			buy_1dq1_text.config(state='normal')
			buy_jita_text.config(state='normal')
			sell_1dq1_text.config(state='normal')
			sell_jita_text.config(state='normal')
			batches_output_text3.config(state='normal')

			# Clear existing content
			buy_1dq1_text.delete('1.0', tk.END)
			buy_jita_text.delete('1.0', tk.END)
			sell_1dq1_text.delete('1.0', tk.END)
			sell_jita_text.delete('1.0', tk.END)
			batches_output_text3.delete('1.0', tk.END)

			# Update with new content
			buy_1dq1_text.insert(tk.END, "\n".join(f"{key.name}: {value}" for key, value in buy_1dq_orders.items()))
			buy_jita_text.insert(tk.END, "\n".join(f"{key.name}: {value}" for key, value in buy_jita_orders.items()))
			sell_1dq1_text.insert(tk.END, "\n".join(f"{key.name}: {value}" for key, value in sell_1dq_orders.items()))
			sell_jita_text.insert(tk.END, "\n".join(f"{key.name}: {value}" for key, value in sell_jita_orders.items()))
			batches_output_text3.insert(tk.END, "\n".join(f"{key.name}: {value}" for key, value in reactions.items()))

			# Disable the Text widgets to prevent user editing
			buy_1dq1_text.config(state='disabled')
			buy_jita_text.config(state='disabled')
			sell_1dq1_text.config(state='disabled')
			sell_jita_text.config(state='disabled')
			batches_output_text3.config(state='disabled')
	def delete_batch():
		selected = selected_batch.get()
		if selected in batches:
			del batches[selected]
			update_batches()
	root = tk.Tk()
	root.title("4sReactions")
	notebook = ttk.Notebook(root)
	notebook.pack(expand=1, fill="both")

	reactionstab = ttk.Frame(notebook)
	notebook.add(reactionstab, text='reactions')

	reactionstab.columnconfigure(0, weight=1)
	reactionstab.columnconfigure(1, weight=1)
	reactionstab.rowconfigure(1, weight=1)
	reactionstab.rowconfigure(2, weight=1)
	reactionstab.rowconfigure(3, weight=90)
	reactionstab.rowconfigure(4, weight=1)

	input_label = ttk.Label(reactionstab, text="Input:")
	input_label.grid(column=0, row=0, padx=10, pady=10, sticky='w')
	input_text = tk.Text(reactionstab, height=10, width=30)
	input_text.grid(column=0, row=1, padx=10, pady=10, rowspan=3, sticky='nsew')

	batch_label = ttk.Label(reactionstab, text="batchname:")
	batch_label.grid(column=1, row=0, padx=10, pady=10, sticky='w')
	batch_name = tk.Text(reactionstab, height=2, width=30)
	batch_name.grid(column=1, row=1, padx=10, pady=10, sticky='nsew')
	output_label = ttk.Label(reactionstab, text="Output:")
	output_label.grid(column=1, row=2, padx=10, pady=10, sticky='w')
	output_text = tk.Text(reactionstab, height=10, width=30, state='disabled')
	output_text.grid(column=1, row=3, padx=10, pady=10, sticky='nsew')
	submit_button = ttk.Button(reactionstab, text="Submit", command=update_output_reactions)
	submit_button.grid(columnspan=2, row=4, pady=10)
	# batches
	batchestab = ttk.Frame(notebook)
	notebook.add(batchestab, text='batches')

	batchestab.columnconfigure(0, weight=1)
	batchestab.columnconfigure(1, weight=1)
	batchestab.columnconfigure(2, weight=1)
	batchestab.columnconfigure(3, weight=1)
	batchestab.rowconfigure(1, weight=9)
	batchestab.rowconfigure(2, weight=1)
	batchestab.rowconfigure(3, weight=9)
	batchestab.rowconfigure(4, weight=1)

	batches_label = ttk.Label(batchestab, text="Select Batch:")
	batches_label.grid(column=0, row=0, padx=10, pady=10, sticky='w')
	batch_options = ['No batches']  # Example batch options
	selected_batch = tk.StringVar(value=batch_options[0])
	batch_dropdown = ttk.Combobox(batchestab, textvariable=selected_batch, values=batch_options)
	batch_dropdown.grid(column=0, row=1, padx=10, pady=10, sticky='nsew')
	batch_delete_button = ttk.Button(batchestab, text="delete batch", command=delete_batch)
	batch_delete_button.grid(column=0, row=2)

	batches_output_label1 = ttk.Label(batchestab, text="1DQ1 Buy Orders:")
	batches_output_label1.grid(column=1, row=0, padx=10, pady=10, sticky='w')
	buy_1dq1_text = tk.Text(batchestab, height=10, width=30, state='disabled')
	buy_1dq1_text.grid(column=1, row=1, padx=10, pady=10, sticky='nsew')
	batches_output_label1 = ttk.Label(batchestab, text="Jita Buy Orders:")
	batches_output_label1.grid(column=1, row=2, padx=10, pady=10, sticky='w')
	buy_jita_text = tk.Text(batchestab, height=10, width=30, state='disabled')
	buy_jita_text.grid(column=1, row=3, padx=10, pady=10, sticky='nsew')

	batches_output_label2 = ttk.Label(batchestab, text="1DQ1 Sell Orders:")
	batches_output_label2.grid(column=2, row=0, padx=10, pady=10, sticky='w')
	sell_1dq1_text = tk.Text(batchestab, height=10, width=30, state='disabled')
	sell_1dq1_text.grid(column=2, row=1, padx=10, pady=10, sticky='nsew')
	batches_output_label2 = ttk.Label(batchestab, text="Jita Sell Orders:")
	batches_output_label2.grid(column=2, row=2, padx=10, pady=10, sticky='w')
	sell_jita_text = tk.Text(batchestab, height=10, width=30, state='disabled')
	sell_jita_text.grid(column=2, row=3, padx=10, pady=10, sticky='nsew')

	batches_output_label3 = ttk.Label(batchestab, text="Reactions:")
	batches_output_label3.grid(column=3, row=0, padx=10, pady=10, sticky='w')
	batches_output_text3 = tk.Text(batchestab, height=10, width=30, state='disabled')
	batches_output_text3.grid(column=3, row=1, padx=10, pady=10, sticky='nsew', rowspan=3)
	batch_dropdown.bind("<<ComboboxSelected>>", update_fields)
	update_batches()
	root.mainloop()
load_or_import_data('sde/fsd/typeIDs.yaml', 'sde/fsd/blueprints.yaml', 'sde/fsd/groupIDs.yaml')
load_types()
get_prices()
get_profits()
ui()