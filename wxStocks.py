import wx, sys, os, csv, time, datetime, logging, ast, math, threading, inspect, urllib2
import cPickle as pickle
from pyql import pyql
from wx.lib import sheet
from BeautifulSoup import BeautifulSoup

class Stock(object):
	def __init__(self, symbol):
		self.symbol = symbol
		self.epoch = float(time.time())
		self.created_epoch = float(time.time())
		self.updated = datetime.datetime.now()
class StockAnnualData(object):
	def __init__(self, symbol):
		self.symbol = symbol
		self.epoch = float(time.time())
		self.created_epoch = float(time.time())
		self.updated = datetime.datetime.now()
		# individual data sheets last update
		self.last_balance_sheet_update = 0
		self.last_income_statement_update = 0
		self.last_cash_flow_update = 0
		self.periods = ["", "", ""]

# Stock Valuation Functions: I use functions, rather than actual methods because they mess up spreadsheets with their superfluous object data
def neff_5_Year_future_estimate(Stock): #incomplete
	'''
	[Dividend Yield% + 5year Estimate of future %% EPS Growth]/PEttm 
	(the last letter "F" in the name stands for "future" estimate, while "H" stands for "historical".)
	'''
	dividend_yield = float(Stock.DividendYield)
	pass # need to find 5 year eps growth %
def neff_TTM_historical(Stock): #incomplete
	'''
	[3 x Dividend Yield% + EPS (from continuing operations) historical Growth over TTM]/PEttm 
	In this formula you can see that I gave triple weight to dividends.  
	I thought that over the short run (TTM) dividends represent stability and "Dividends don't lie".
	-- Robert Schoolfield
	'''
	annual_data = return_existing_StockAnnualData(Stock.symbol)
	if not annual_data:
		print "You must update annual data for %s" % Stock.symbol
		return
	dividend_yield = float(Stock.DividendYield)

	income_from_continuing_operations = annual_data.Net_Income_From_Continuing_Ops
	weighted_avg_common_shares = "???"
	eps_from_contiuning_operations = income_from_continuing_operations/weighted_avg_common_shares

	pe_ttm = "blah this needs to be figured out"
	pass
def marginPercentRank(Stock, stock_list): #incomplete
	'''
	"Percent" Rank of Net Margin where Highest Margin = 100%% and Lowest = 0%

	"Percent" Rank = ([Numerical Rank]/[Total Count of Numbers Ranked]) x 100
	If you are ranking 500 different companies, then [Total Count of Numbers Ranked] = 500
	'''
	pass
def roePercentRank(Stock, stock_list): #incomplete
	'''
	%% Rank of Return on Equity.
	Bigger is better.
	'''
	pass
def roePercentDev(Stock):
	'''
	Coefficient of Variation for (ROE(Y1), ROE(Y2), ROE(Y3)) 

	= [Standard Deviation of (ROE(Y1), ROE(Y2), ROE(Y3))]/[Average of (ROE(Y1), ROE(Y2), ROE(Y3))]  
	This determines how "smooth" the graph is of ROE for the three different years.  
	Less than one is "smooth" while greater than one is "not smooth".
	It also determines if the average ROE over the three years is significantly greater than zero. 
	'''
	pass
def price_to_book_growth(Stock):
	'''
	= Price Growth(over last 3 fiscal years)/Book Value Growth(over last 3 fiscal years)
	= (Price(Y1)/Price(Y3)) / (Book Value(Y1)/Book Value(Y3))
	= (Price(Y1)/Price(Y3)) x (Book Value(Y3)/Book Value(Y1))
	
	This is a ratio that Warren Buffet likes, so I thought I would throw it in.  
	He says it tells him if growth in the Book Value of the company is reflected in the Price growth.  
	He likes it around 1.
	'''
	pass
def kGrowth(Stock): # incomplete, no definition yet
	pass
def price_to_range(Stock):
	'''
	= Price to (52 Week Price Range) 
	= ([Current Price] - [52 wk Low Price]) / ([52 wk High Price] - [52 wk Low Price])

	If the current price is close to its 52 wk Low Price, then Prc2Rng is close to zero.
	If the current price is close to its 52 wk High Price, then Prc2Rng is close to one.
	If the current price is half way between its 52 wk High Price and its 52 wk Low Price, 
	then Prc2Rng is close to 0.5.

	I like to have it greater than 0.2.
	'''
	pass
def percentage_held_by_insiders(Stock):
	try:
		if Stock.PercentageHeldbyInsiders:
			percentage_held_by_insiders = float(Stock.PercentageHeldbyInsiders)
			return percentage_held_by_insiders
	except Exception, exception:
		print line_number(), exception
		return None
def percentage_held_by_institutions(Stock): # this may no be necessary
	try:
		if Stock.PercentageHeldbyInstitutions:
			percentage_held_by_institutions = float(Stock.PercentageHeldbyInstitutions)
			return percentage_held_by_institutions
	except Exception, exception:
		print line_number(), exception
		return None
def current_ratio(Stock):
	try:
		if Stock.CurrentRatio_mrq:
			current_ratio = float(Stock.CurrentRatio_mrq)
			return current_ratio
	except Exception, exception:
		print line_number(), exception
		return None
def longTermDebtToEquity(Stock):
	annual_data = return_existing_StockAnnualData(Stock)
	long_term_debt = annual_data.Long_Term_Debt
	equity = annual_data.Total_Stockholder_Equity
	if long_term_debt == "-":
		long_term_debt = 0.00
	else:
		long_term_debt = float(long_term_debt)
	if equity == "-":
		print 'Cannot divide by zero'
		return "None"
	else:
		equity = float(equity)
	return float(long_term_debt/equity)
def neffEvEBIT(Stock):
	'''
	Neff ratio replacing Earnings with EBIT and PE with [Enterprise Value/EBIT]. 
	With a double weight on Dividends.  
	(Data reported by database for Enterprise Value and EBIT are not per share, but it doesn't matter because:
	[Enterprise Value/EBIT] = [Enterprise Value per share]/[EBIT per share]
	i.e. # of shares cancels in the ratio.  
	Also:
	[EBIT growth %] = [EBIT per share growth %] 
	are dimensionless ratios (written as percents).
	
	EBIT growth %% is calculated as the percent growth in EBIT (over 3 years) 
	from the 4th fiscal year (Y5) before the most recent fiscal year (Y1) 
	to the first fiscal year (Y2) before the most recent fiscal year(Y1).  
	Why I didn't use Y1 I can't remember. The exact name of 
	EBIT growth% = (([EBIT Y2]/[EBIT Y5]-1)^(1/3)) x 100  
	(The 100 makes it a percentage value.)

	So NeffEv EBIT = (2 x [DivYield%] + [EBIT Growth%])/([Enterprise Value]/[EBIT])
	'''
	pass
def neffCf3Year(Stock):
	'''
	(3 year Historical) Neff ratio where Earnings/Share is replaced by CashFlow/Share.
	'''
	pass

# Stock Annual Date Scraping Functions
# ---- unfortunately after scraping many stocks, these scraping functions need to be overhauled
# ---- it seems that the data that is returned is not formatted properly for firms that are < 4 years old
# ---- I'll need to account for this disparity and rewrite the scrape functions with more precision.
## --- Much has been improved, but i still need to do a re-write it for single year data.
def scrape_balance_sheet_income_statement_and_cash_flow(list_of_ticker_symbols):
	one_day = (60 * 60 * 24)
	yesterdays_epoch = float(time.time()) - one_day
	ticker_list = list_of_ticker_symbols
	edited_ticker_list = []
	for ticker in ticker_list:
		stock = return_existing_StockAnnualData(ticker)
		if stock:
			if stock.last_cash_flow_update > yesterdays_epoch and stock.last_income_statement_update > yesterdays_epoch and stock.last_balance_sheet_update > yesterdays_epoch: # if data is more than a day old
				print "%s is up to date (no need to update)" % ticker
				continue # if all are up to date skip ahead, and don't append ticker
		edited_ticker_list.append(ticker)
	ticker_list = edited_ticker_list
	if ticker_list:
		print "updating:", ticker_list

	for i in range(len(ticker_list)):
		# 2 second sleep per scrape
		# timer = count * 6 + position of data needed, function, ticker
		timer_1 = threading.Timer((i * 6)+1, yahoo_annual_balance_sheet_scrape, [ticker_list[i]])
		timer_2 = threading.Timer((i * 6)+3, yahoo_annual_income_statement_scrape, [ticker_list[i]])
		timer_3 = threading.Timer((i * 6)+5, yahoo_annual_cash_flow_scrape, [ticker_list[i]])
		timer_1.start()
		timer_2.start()
		timer_3.start()
def yahoo_annual_cash_flow_scrape(ticker):

	stock = return_existing_StockAnnualData(ticker)
	if stock:
		yesterdays_epoch = float(time.time()) - (60 * 60 * 24)
		if stock.last_cash_flow_update > yesterdays_epoch: # if data is more than a day old
			print "Cash flow data for %s is up to date." % ticker
			return

	soup = BeautifulSoup(urllib2.urlopen('http://finance.yahoo.com/q/cf?s=%s&annual' % ticker), convertEntities=BeautifulSoup.HTML_ENTITIES)
	factor = 0
	thousands = soup.body.findAll(text= "All numbers in thousands")
	if thousands:
		factor = 1000

	if not factor:
		print "Error: no factor... in need of review"

	table = soup.find("table", { "class" : "yfnc_tabledata1" })

	data_list = []

	find_all_data_in_table(table, "td", data_list, factor)
	find_all_data_in_table(table, "strong", data_list, factor)

	create_or_update_StockAnnualData(ticker, data_list, "Cash_Flow")

	cash_flow_layout = 	['''
					0	Period Ending
					1	Period Ending
					2	-
					3	-
					4	-
					5	Operating Activities, Cash Flows Provided By or Used In
					6	Depreciation
					7	-
					8	-
					9	-
					10	Adjustments To Net Income
					11	-
					12	-
					13	-
					14	Changes In Accounts Receivables
					15	-
					16	-
					17	-
					18	Changes In Liabilities
					19	-
					20	-
					21	-
					22	Changes In Inventories
					23	-
					24	-
					25	-
					26	Changes In Other Operating Activities
					27	-
					28	-
					29	-
					30	Investing Activities, Cash Flows Provided By or Used In
					31	Capital Expenditures
					32	-
					33	-
					34	-
					35	Investments
					36	-
					37	-
					38	-
					39	Other Cash flows from Investing Activities
					40	-
					41	-
					42	-
					43	Financing Activities, Cash Flows Provided By or Used In
					44	Dividends Paid
					45	-
					46	-
					47	-
					48	Sale Purchase of Stock
					49	-
					50	-
					51	-
					52	Net Borrowings
					53	-
					54	-
					55	-
					56	Other Cash Flows from Financing Activities
					57	-
					58	-
					59	-
					60	Effect Of Exchange Rate Changes
					61	-
					62	-
					63	-
					64	Net Income
					65	-
					66	-
					67	-
					68	Operating Activities, Cash Flows Provided By or Used In
					69	Total Cash Flow From Operating Activities
					70	-
					71	-
					72	-
					73	Investing Activities, Cash Flows Provided By or Used In
					74	Total Cash Flows From Investing Activities
					75	-
					76	-
					77	-
					78	Financing Activities, Cash Flows Provided By or Used In
					79	Total Cash Flows From Financing Activities
					80	-
					81	-
					82	-
					83	Change In Cash and Cash Equivalents
					84	-
					85	-
					86	-
						''']
def yahoo_annual_income_statement_scrape(ticker):

	stock = return_existing_StockAnnualData(ticker)
	if stock:
		yesterdays_epoch = float(time.time()) - (60 * 60 * 24)
		if stock.last_income_statement_update > yesterdays_epoch: # if data is more than a day old
			print "Income statement data for %s is up to date." % ticker
			return

	soup = BeautifulSoup(urllib2.urlopen('http://finance.yahoo.com/q/is?s=%s&annual' % ticker), convertEntities=BeautifulSoup.HTML_ENTITIES)
	factor = 0
	thousands = soup.body.findAll(text= "All numbers in thousands")
	if thousands:
		factor = 1000

	table = soup.find("table", { "class" : "yfnc_tabledata1" })

	data_list = []


	find_all_data_in_table(table, "td", data_list, factor)
	find_all_data_in_table(table, "strong", data_list, factor)

	create_or_update_StockAnnualData(ticker, data_list, "Income_Statement")

	income_statment_layout = 	['''
							0	Period Ending
							1	Period Ending
							2	Cost of Revenue
							3	-
							4	-
							5	-
							6	Operating Expenses
							7	Research Development
							8	-
							9	-
							10	-
							11	Selling General and Administrative
							12	-
							13	-
							14	-
							15	Non Recurring
							16	-
							17	-
							18	-
							19	Others
							20	-
							21	-
							22	-
							23	Total Operating Expenses
							24	-
							25	-
							26	-
							27	Income from Continuing Operations
							28	Total Other Income/Expenses Net
							29	-
							30	-
							31	-
							32	Earnings Before Interest And Taxes
							33	-
							34	-
							35	-
							36	Interest Expense
							37	-
							38	-
							39	-
							40	Income Before Tax
							41	-
							42	-
							43	-
							44	Income Tax Expense
							45	-
							46	-
							47	-
							48	Minority Interest
							49	-
							50	-
							51	-
							52	Net Income From Continuing Ops
							53	-
							54	-
							55	-
							56	Non-recurring Events
							57	Discontinued Operations
							58	-
							59	-
							60	-
							61	Extraordinary Items
							62	-
							63	-
							64	-
							65	Effect Of Accounting Changes
							66	-
							67	-
							68	-
							69	Other Items
							70	-
							71	-
							72	-
							73	Preferred Stock And Other Adjustments
							74	-
							75	-
							76	-
							77	Total Revenue
							78	-
							79	-
							80	-
							81	Gross Profit
							82	-
							83	-
							84	-
							85	Operating Income or Loss
							86	-
							87	-
							88	-
							89	Net Income
							90	-
							91	-
							92	-
							93	Net Income Applicable To Common Shares
							94	-
							95	-
							96	-
								''']
def yahoo_annual_balance_sheet_scrape(ticker):

	stock = return_existing_StockAnnualData(ticker)
	if stock:
		yesterdays_epoch = float(time.time()) - (60 * 60 * 24)
		if stock.last_balance_sheet_update > yesterdays_epoch: # if data is more than a day old
			print "Balance sheet data for %s is up to date." % ticker
			return

	soup = BeautifulSoup(urllib2.urlopen('http://finance.yahoo.com/q/bs?s=%s&annual' % ticker), convertEntities=BeautifulSoup.HTML_ENTITIES)
	factor = 0
	thousands = soup.body.findAll(text= "All numbers in thousands")
	if thousands:
		factor = 1000
	table = soup.find("table", { "class" : "yfnc_tabledata1" })

	data_list = []

	find_all_data_in_table(table, "td", data_list, factor)
	find_all_data_in_table(table, "strong", data_list, factor)

	create_or_update_StockAnnualData(ticker, data_list, "Balance_Sheet")

	balance_sheet_layout = 	['''
							0	Period Ending
							1	Period Ending
							2	Mar 31 2013
							3	Mar 31 2012
							4	Mar 31 2011
							5	Assets
							6	Current Assets
							7	Cash And Cash Equivalents
							8	4059000000
							9	4047000000
							10	3767000000
							11	Short Term Investments
							12	320000000
							13	74000000
							14	32000000
							15	Net Receivables
							16	1754000000
							17	1524000000
							18	1322000000
							19	Inventory
							20	-
							21	-
							22	-
							23	Other Current Assets
							24	391000000
							25	300000000
							26	206000000
							27	Long Term Investments
							28	72000000
							29	2000000
							30	5000000
							31	Property Plant and Equipment
							32	1191000000
							33	1063000000
							34	1086000000
							35	Goodwill
							36	364000000
							37	195000000
							38	185000000
							39	Intangible Assets
							40	68000000
							41	34000000
							42	11000000
							43	Accumulated Amortization
							44	-
							45	-
							46	-
							47	Other Assets
							48	245000000
							49	236000000
							50	326000000
							51	Deferred Long Term Asset Charges
							52	94000000
							53	62000000
							54	85000000
							55	Liabilities
							56	Current Liabilities
							57	Accounts Payable
							58	393000000
							59	310000000
							60	224000000
							61	Short/Current Long Term Debt
							62	-
							63	9000000
							64	-
							65	Other Current Liabilities
							66	765000000
							67	618000000
							68	592000000
							69	Long Term Debt
							70	-
							71	-
							72	-
							73	Other Liabilities
							74	27000000
							75	22000000
							76	72000000
							77	Deferred Long Term Liability Charges
							78	23000000
							79	2000000
							80	-
							81	Minority Interest
							82	-
							83	-
							84	-
							85	Negative Goodwill
							86	-
							87	-
							88	-
							89	Stockholders' Equity
							90	Misc Stocks Options Warrants
							91	-
							92	-
							93	-
							94	Redeemable Preferred Stock
							95	-
							96	-
							97	-
							98	Preferred Stock
							99	-
							100	-
							101	-
							102	Common Stock
							103	64000000
							104	64000000
							105	64000000
							106	Retained Earnings
							107	7666000000
							108	6509000000
							109	5294000000
							110	Treasury Stock
							111	-
							112	-
							113	-
							114	Capital Surplus
							115	-
							116	-
							117	-
							118	Other Stockholder Equity
							119	-399000000
							120	3000000
							121	764000000
							122	Assets
							123	Total Current Assets
							124	6505000000
							125	5945000000
							126	5312000000
							127	Total Assets
							128	8539000000
							129	7537000000
							130	7010000000
							131	Liabilities
							132	Total Current Liabilities
							133	1158000000
							134	937000000
							135	816000000
							136	Total Liabilities
							137	1208000000
							138	961000000
							139	888000000
							140	Stockholders' Equity
							141	Total Stockholder Equity
							142	-
							143	-
							144	-
							145	Net Tangible Assets
							146	-
							147	-
							148	-
							''']	
def find_all_data_in_table(table, str_to_find, data_list_to_append_to, table_factor):
	for cell in table.findAll(str_to_find):
		text = cell.find(text=True)
		if text:
			text = strip_string_whitespace(text)
			text = text.replace(u'\xa0', u' ')
			text = str(text)
			text = text.replace(',', "")
			if text:
				if text[0] == "(":
					text_list = list(text)
					text_list[0] = "-"
					text_list[-1] = ""
					text = "".join(text_list)
			if is_number(text):
				text_float = float(text) * table_factor
				if relevant_float(text_float):
					text = str(text_float)
				else:
					text = str(int(text_float))

			#if text == "Period Ending":
			#	dates = table.findAll("th")
			#	for date in dates:
			#		print date
		if text:
			#print text
			data_list_to_append_to.append(str(text))
def return_existing_StockAnnualData(ticker_symbol):
	global GLOBAL_ANNUAL_DATA_STOCK_LIST
	for stock in GLOBAL_ANNUAL_DATA_STOCK_LIST:
		if stock.symbol == ticker_symbol:
			return stock
	#if the function does not return a stock
	return None
def create_or_update_StockAnnualData(ticker, data_list, data_type):
	print "--------------"
	print data_type
	print len(data_list)
	#print data_list

	# ?????????????????????????

	stock = return_existing_StockAnnualData(ticker)
	if not stock:
		stock = StockAnnualData(ticker)
		GLOBAL_ANNUAL_DATA_STOCK_LIST.append(stock)


	# yahoo balance sheet loop
	default_amount_of_data = 3
	cash_flow_data_positions = [1,6,10,14,18,22,26,31,35,39,44,48,52,56,60,64,69,74,79,83]
	income_statement_data_postitions = [2,7,11,15,19,23,28,32,36,40,44,48,52,57,61,65,69,73,77,81,85,89,93]
	balance_sheet_data_positions = [1,7,11,15,19,23,27,31,35,39,43,47,51,57,61,65,69,73,77,81,85,90,94,98,102,106,110,114,118,123,127,132,136,141,145]
	# unless data list format is irregular
	# What i'm doing here is complicated, if there are only two units of data
	# in each data position i need to adjust the position of the list from which to grab
	# the data. This is actually a fairly simple iteration. 
	# If the data is different by 1 unit of data per section
	# the adjustment is to change the position by 1, for each section.
	# This creates a compounding adjustment, increasing by 1 unit each time,
	# made simple by increasing the adjustment variable each pass.
	#print "len(data_list) =", len(data_list), data_list
	if data_type == "Balance_Sheet" and len(data_list) == 117:#96:
		print "adjusting for 2 years worth of Balance_Sheet data"
		default_amount_of_data = 2
		adjusted_balance_sheet_data_positions = []
		adjustment_variable = 0
		for i in balance_sheet_data_positions:
			adjusted_balance_sheet_data_positions.append(i - adjustment_variable)
			adjustment_variable += 1
		balance_sheet_data_positions = adjusted_balance_sheet_data_positions
		#print balance_sheet_data_positions
	elif data_type == "Income_Statement" and len(data_list) == 74:#59:
		print "adjusting for 2 years worth of Income_Statement data"
		default_amount_of_data = 2
		adjusted_income_statement_data_positions = []
		adjustment_variable = 0
		for i in income_statement_data_postitions:
			adjusted_income_statement_data_positions.append(i - adjustment_variable)
			adjustment_variable += 1
		income_statement_data_postitions = adjusted_income_statement_data_positions
		#print income_statement_data_postitions
	elif data_type == "Cash_Flow" and len(data_list) == 67:
		print "adjusting for 2 years worth of Cash_Flow data"
		default_amount_of_data = 2
		adjusted_cash_flow_data_positions = []
		adjustment_variable = 0
		for i in cash_flow_data_positions:
			adjusted_cash_flow_data_positions.append(i - adjustment_variable)
			adjustment_variable += 1
		cash_flow_data_positions = adjusted_cash_flow_data_positions
		#print cash_flow_data_positions

	data_positions = []
	if data_type == "Cash_Flow":
		data_positions = cash_flow_data_positions
		stock.last_cash_flow_update = float(time.time())
	elif data_type == "Balance_Sheet":
		for i in data_list:
			print i
		data_positions = balance_sheet_data_positions
		stock.last_balance_sheet_update = float(time.time())
	elif data_type == "Income_Statement":
		data_positions = income_statement_data_postitions
		stock.last_income_statement_update = float(time.time())
	else:
		print "no data type selected"
		return

	# First, define period
	if stock:
		for i in range(len(data_list)):
			if i in data_positions:
				attribute = str(data_list[i])					
				attribute = attribute.replace(" ","_")
				attribute = attribute.replace("/","_")
				attribute = attribute.replace("'","")
				if attribute == "Period_Ending":
					for j in range(default_amount_of_data):
						data = data_list[i+j+1]
						#print data
						data = data[-4:]
						#print data
						stock.periods[j] = data
	########

	for i in range(len(data_list)):
		if i in data_positions:
			# attribute
			attribute = str(data_list[i])
			
			#print attribute
			
			attribute = attribute.replace(" ","_")
			attribute = attribute.replace("/","_")
			attribute = attribute.replace("'","")
			if attribute == "Period_Ending":
				attribute = attribute + "_For_" + data_type
			attribute_data_list = []
			#print "default amount of data =", default_amount_of_data
			for j in range(default_amount_of_data):
				data = data_list[i+j+1]
				data = data.replace(",","")

				#print data

				#try:
				#	data = int(data)
				#except:
				#	# data is not a number
				#	pass
				attribute_data_list.append(data)
			
			year_fail_list = ["", "20XX", "20YY"]
			for k in range(default_amount_of_data):
				year = ""
				if k != 0:
					year = stock.periods[k]
					if not year:
						year = year_fail_list[k]
					year = "_" + year
				setattr(stock, attribute + year, attribute_data_list[k])

	for attribute in dir(stock):
		if not attribute.startswith("_"):
			print ticker+"."+attribute+":" , getattr(stock, attribute)
	
	with open('all_annual_data_stocks.pk', 'wb') as output:
		pickle.dump(GLOBAL_ANNUAL_DATA_STOCK_LIST, output, pickle.HIGHEST_PROTOCOL)
###

class HeldStock(object):
	def __init__(self, symbol, quantity, security_type):
		self.symbol = symbol
		self.quantity = quantity
		self.security_type = security_type
		self.cost_basis = None
class Account(object):
	def __init__(self, id_number, cash, stock_list):
		self.id_number = id_number
		self.availble_cash = cash # there is a ticker "CASH" that already exists, ugh		
		self.stock_list = stock_list
		for stock in self.stock_list:
			setattr(self, stock.symbol, stock)
def line_number():
    """Returns the current line number in our program."""
    line_number = inspect.currentframe().f_back.f_lineno
    line_number_string = "Line %d:" % line_number
    return line_number_string

try:
	ticker_list = open('ticker.pk', 'rb')
except Exception, e:
	print line_number(), e
	ticker_list = open('ticker.pk', 'wb')
	ticker_list = []
	with open('ticker.pk', 'wb') as output:
		pickle.dump(ticker_list, output, pickle.HIGHEST_PROTOCOL)
	ticker_list = open('ticker.pk', 'rb')
GLOBAL_TICKER_LIST = pickle.load(ticker_list)
ticker_list.close()
try:
	stock_list = open('all_stocks.pk', 'rb')
except Exception, e:
	print line_number(), e
	stock_list = open('all_stocks.pk', 'wb')
	stock_list = []
	with open('all_stocks.pk', 'wb') as output:
		pickle.dump(stock_list, output, pickle.HIGHEST_PROTOCOL)
	stock_list = open('all_stocks.pk', 'rb')
GLOBAL_STOCK_LIST = pickle.load(stock_list)
stock_list.close()

try:
	annual_data_stock_list = open('all_annual_data_stocks.pk', 'rb')
except Exception, e:
	print e
	annual_data_stock_list = open('all_annual_data_stocks.pk', 'wb')
	annual_data_stock_list = []
	with open('all_annual_data_stocks.pk', 'wb') as output:
		pickle.dump(annual_data_stock_list, output, pickle.HIGHEST_PROTOCOL)
	annual_data_stock_list = open('all_annual_data_stocks.pk', 'rb')
GLOBAL_ANNUAL_DATA_STOCK_LIST = pickle.load(annual_data_stock_list)
annual_data_stock_list.close()

SCRAPE_CHUNK_LENGTH = 50
SCRAPE_SLEEP_TIME = 18
TIME_ALLOWED_FOR_BEFORE_RECENT_UPDATE_IS_STALE = float(60*60* 4) # 4 hours
SCREEN_LIST = []
try:
	data_from_portfolios_file = open('portfolios.pk', 'rb')
except Exception, e:
	print line_number(), e
	data_from_portfolios_file = open('portfolios.pk', 'wb')
	data_from_portfolios_file = [1,["Primary"]]
	with open('portfolios.pk', 'wb') as output:
		pickle.dump(data_from_portfolios_file, output, pickle.HIGHEST_PROTOCOL)
	data_from_portfolios_file = open('portfolios.pk', 'rb')
DATA_ABOUT_PORTFOLIOS = pickle.load(data_from_portfolios_file
									# DATA_ABOUT_PORTFOLIOS = 	[
									#								NUMBER_OF_PORTFOLIOS, # this is an integer
									#								[
									#									"Portfolio Name", # string
									#									etc...
									#								]
									#							]
									)
data_from_portfolios_file.close()
NUMBER_OF_PORTFOLIOS = DATA_ABOUT_PORTFOLIOS[0]	
PORTFOLIO_NAMES = []
for i in range(NUMBER_OF_PORTFOLIOS):
	try:
		PORTFOLIO_NAMES.append(DATA_ABOUT_PORTFOLIOS[1][i])
	except Exception, exception:
		print line_number(), exception
		logging.error('Portfolio names do not match number of portfolios')
PORTFOLIO_OBJECTS_LIST = []
for i in range(NUMBER_OF_PORTFOLIOS):
	try:
		portfolio_account_obj_file = open('portfolio_%d_data.pk' % (i+1), 'rb')
		portfolio_obj = pickle.load(portfolio_account_obj_file)
		portfolio_account_obj_file.close()
		PORTFOLIO_OBJECTS_LIST.append(portfolio_obj)
	except Exception, e:
		print line_number(), e
IRRELEVANT_ATTRIBUTES = ["updated",
						"epoch",
						"TradeDate",
						"created_epoch",
						"TrailingPE_ttm_Date",
						"TradeDate",
						"TwoHundreddayMovingAverage",
						"TickerTrend",
						"SharesOwned",
						"SP50052_WeekChange",
						"PricePaid",
						"PercentChangeFromTwoHundreddayMovingAverage",
						"PercentChangeFromFiftydayMovingAverage",
						"PercentChange",
						"PERatioRealtime",
						"OrderBookRealtime",
						"Notes",
						"MostRecentQuarter_mrq",
						"MoreInfo",
						"MarketCapRealtime",
						"LowLimit",
						"LastTradeWithTime",
						"LastTradeTime",
						"LastTradeRealtimeWithTime",
						"LastTradePriceOnly",
						"LastTradeDate",
						"HoldingsValueRealtime",
						"HoldingsValue",
						"HoldingsGainRealtime",
						"HoldingsGainPercentRealtime",
						"HoldingsGainPercent",
						"HoldingsGain",
						"HighLimit",
						"ExDividendDate",
						"DividendPayDate",
						"DaysValueChangeRealtime",
						"DaysValueChange",
						"DaysRangeRealtime",
						"DaysRange",
						"DaysLow",
						"DaysHigh",
						"Commission",
						"Change_PercentChange",
						"ChangeRealtime",
						"ChangePercentRealtime",
						"ChangeFromTwoHundreddayMovingAverage",
						"ChangeFromFiftydayMovingAverage",
						"Change",
						"ChangeinPercent",
						"BidRealtime",
						"Bid",
						"AvgVol_3_month",
						"AvgVol_10_day",
						"AskRealtime",
						"Ask",
						"AnnualizedGain",
						"AfterHoursChangeRealtime",
						"52_WeekLow_Date",
						"52_WeekLow",
						"52_WeekHigh_Date",
						"52_WeekHigh",
						"52_WeekChange",
						"50_DayMovingAverage",
						"200_DayMovingAverage"
						]

DEFAULT_ROWS_ON_SALES_PREP_PAGE = 9
DEFAULT_ROWS_ON_TRADE_PREP_PAGE_FOR_TICKERS = 6
SALE_PREP_PORTFOLIOS_AND_SALE_CANDIDATES_TUPLE = [[],[]] # [[relevant portfolios list], [sale ticker|#shares tuple list]]

# with open('dummy.pk', 'wb') as output:
#	pickle.dump(SOME_DATA, output, pickle.HIGHEST_PROTOCOL)

class GridAllStocks(wx.grid.Grid):
	def __init__(self, *args, **kwargs):
		wx.grid.Grid.__init__(self, *args, **kwargs)
		global GLOBAL_STOCK_LIST
		self.num_rows = len(GLOBAL_STOCK_LIST)
		self.num_columns = 0
		for stock in GLOBAL_STOCK_LIST:
			num_attributes = 0
			for attribute in dir(stock):
				if not attribute.startswith('_'):
					num_attributes += 1
			if self.num_columns < num_attributes:
				self.num_columns = num_attributes
		#print line_number(), "Number of rows: %d" % self.num_rows
		#print line_number(), "Number of columns: %d" % self.num_columns
class StockScreenGrid(wx.grid.Grid):
	def __init__(self, *args, **kwargs):
		wx.grid.Grid.__init__(self, *args, **kwargs)
		
		global SCREEN_LIST
		stock_list = SCREEN_LIST

		self.num_rows = len(stock_list)
		self.num_columns = 0
		for stock in stock_list:
			num_attributes = 0
			for attribute in dir(stock):
				if not attribute.startswith('_'):
					num_attributes += 1
			if self.num_columns < num_attributes:
				self.num_columns = num_attributes
				#print line_number(), num_attributes
		#print line_number(), "Number of rows: %d" % self.num_rows
		#print line_number(), "Number of columns: %d" % self.num_columns
class SalePrepGrid(wx.grid.Grid):
	def __init__(self, *args, **kwargs):
		wx.grid.Grid.__init__(self, *args, **kwargs)
class TradeGrid(wx.grid.Grid):
	def __init__(self, *args, **kwargs):
		wx.grid.Grid.__init__(self, *args, **kwargs)
class AccountDataGrid(wx.grid.Grid):
	def __init__(self, *args, **kwargs):
		wx.grid.Grid.__init__(self, *args, **kwargs)

class MainFrame(wx.Frame):
	def __init__(self, *args, **kwargs):
		wx.Frame.__init__(self, None, title="wxStocks", *args, **kwargs)

		# Here we create a panel and a notebook on the panel
		main_frame = wx.Panel(self)
		notebook = wx.Notebook(main_frame)

		# create the page windows as children of the notebook
		# add the pages to the notebook with the label to show on the tab
		self.welcome_page = WelcomePage(notebook)
		notebook.AddPage(self.welcome_page, "Welcome")

		self.ticker_list_page = TickerPage(notebook)
		notebook.AddPage(self.ticker_list_page, "Tickers")

		self.scrape_page = ScrapePage(notebook)
		notebook.AddPage(self.scrape_page, "Scrape")

		self.all_stocks_page = AllStocksPage(notebook)
		notebook.AddPage(self.all_stocks_page, "Stocks")

		self.stock_screen_page = ScreenPage(notebook)
		notebook.AddPage(self.stock_screen_page, "Screen")

		self.saved_screen_page = SavedScreenPage(notebook)
		notebook.AddPage(self.saved_screen_page, "Saved Screens")

		self.rank_page = RankPage(notebook)
		notebook.AddPage(self.rank_page, "Rank")

		self.sale_prep_page = SalePrepPage(notebook)
		notebook.AddPage(self.sale_prep_page, "Sale Prep")

		self.trade_page = TradePage(notebook)
		notebook.AddPage(self.trade_page, "Trade")

		self.portfolio_page = PortfolioPage(notebook)
		notebook.AddPage(self.portfolio_page, "Portfolio")

		# finally, put the notebook in a sizer for the panel to manage
		# the layout


		sizer = wx.BoxSizer()
		sizer.Add(notebook, 1, wx.EXPAND)
		main_frame.SetSizer(sizer)
class Tab(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)

class WelcomePage(Tab):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)
		welcome_page_text = wx.StaticText(self, -1, 
							 "Welcome to wxStocks", 
							 (10,10)
							 )
		instructions_text = '''

	Instructions: 	this program is essentially a work-flow following the tabs above.
	---------------------------------------------------------------------------------------------------------------------------------

	Tickers:		This page is where you load in a .CSV file to create a list of tickers to scrape.
				You can get a properly formatted .CSV from the exchanges you want via a link on this page.

	Scrape:		This page takes the tickers, and then scrapes current stock data using them.

	Stocks:		This page generates a list of all stocks that have been scraped and presents all the data about them.
				Use this page to double check your data to make sure it's accurate and up to date.

	Screen:		This page allows you to screen for stocks that fit your criteria, and save them for later.

	Saved Screens:	This page allows you to recall old screens you've saved.

	Rank:		This page allows you to rank stocks along certain criteria. 

	Sale Prep:	This page allows you to estimate the amount of funds generated from a potential stock sale.

	Trade:		This page (currently not functional) takes the stocks you plan to sell, estimates the amount of money generated, 
				and lets you estimate the volume of stocks to buy to satisfy your diversification requirements.

	Portfolio:	This page allows you to load your portfolios from which you plan on making trades.
				If you have more than one portfolio you plan on working from, you may add more.
	'''

		instructions = wx.StaticText(self, -1, 
									instructions_text, 
									(10,20)
									)
class TickerPage(Tab):
	def __init__(self, parent):
		self.ticker_list_file = None

		wx.Panel.__init__(self, parent)
		text = wx.StaticText(self, -1, 
							 "Welcome to the ticker page. Download correctly formatted .csv files here:", 
							 (10,10)
							 )
		link_button = wx.Button(self, label="nasdaq.com/screening/company-list", pos=(472,5), size=(-1,-1))
		link_button.Bind(wx.EVT_BUTTON, self.linkToTickerCSV, link_button) 

		self.showTickerCSV()

	def linkToTickerCSV(self, e):
		wx.LaunchDefaultBrowser("http://www.nasdaq.com/screening/company-list.aspx")

	def showTickerCSV(self):
		global GLOBAL_TICKER_LIST

		self.displayTickers(GLOBAL_TICKER_LIST)

		add_button = wx.Button(self, label="Add .csv", pos=(10,50), size=(-1,-1))
		add_button.Bind(wx.EVT_BUTTON, self.addCsv, add_button) 

		clear_button = wx.Button(self, label="Delete ticker list", pos=(100,50), size=(-1,-1))
		clear_button.Bind(wx.EVT_BUTTON, self.deleteTickerList, clear_button) 

		self.Show()

	def deleteTickerList(self,e):
		'''delete current ticker list'''
		global GLOBAL_TICKER_LIST
		GLOBAL_TICKER_LIST = []
		# opening the file with w+ mode truncates the file
		with open('ticker.pk', 'wb') as output:
			pickle.dump(GLOBAL_TICKER_LIST, output, pickle.HIGHEST_PROTOCOL)
		self.showTickerCSV()

	def addCsv(self, e):
		'''append a csv to current ticker list'''
		self.dirname = ''
		dialog = wx.FileDialog(self, "Choose a file", self.dirname, "", "*.csv", wx.OPEN)
		if dialog.ShowModal() == wx.ID_OK:
			self.filename = dialog.GetFilename()
			self.dirname = dialog.GetDirectory()
			
			new_ticker_file = open(os.path.join(self.dirname, self.filename), 'rb')
			tickers_to_append = gen_ticker_list(new_ticker_file)
			new_ticker_file.close()

			global GLOBAL_TICKER_LIST
			GLOBAL_TICKER_LIST = GLOBAL_TICKER_LIST + tickers_to_append
			GLOBAL_TICKER_LIST = remove_list_duplicates(GLOBAL_TICKER_LIST)
			GLOBAL_TICKER_LIST.sort()
			with open('ticker.pk', 'wb') as output:
				pickle.dump(GLOBAL_TICKER_LIST, output, pickle.HIGHEST_PROTOCOL)
			self.showTickerCSV()
		dialog.Destroy()

	def displayTickers(self, ticker_list):
		ticker_list.sort()
		ticker_list_massive_str = ""
		for ticker in ticker_list:
			ticker_list_massive_str += ticker
			ticker_list_massive_str += ", "
		height_var = 100
		file_display = wx.TextCtrl(self, -1, 
									ticker_list_massive_str, 
									(10, height_var),
									size = (765, 625),
									style = wx.TE_READONLY | wx.TE_MULTILINE ,
									)
class ScrapePage(Tab):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)
		text = wx.StaticText(self, -1, 
							 "Welcome to the scrape page", 
							 (10,10)
							 )
		self.scrape_button = wx.Button(self, label="Scrape YQL", pos=(5,100), size=(-1,-1))
		self.scrape_button.Bind(wx.EVT_BUTTON, self.confirmScrape, self.scrape_button)

		self.abort_scrape_button = wx.Button(self, label="Cancel Scrape", pos=(5,100), size=(-1,-1))
		self.abort_scrape_button.Bind(wx.EVT_BUTTON, self.abortScrape, self.abort_scrape_button)
		self.abort_scrape_button.Hide()
		self.abort_scrape = False

		self.progress_bar = wx.Gauge(self, -1, 100, size=(995, -1), pos = (0, 200))
		self.progress_bar.Hide()
		
		global GLOBAL_TICKER_LIST
		global SCRAPE_SLEEP_TIME
		global SCRAPE_CHUNK_LENGTH
		sleep_time = SCRAPE_SLEEP_TIME

		#if not GLOBAL_TICKER_LIST:
		#	ticker_file = open('ticker.pk', 'rb')
		#	if ticker_file:
		#		GLOBAL_TICKER_LIST = gen_ticker_list(ticker_file)
		#	ticker_file.close()
		ticker_len = len(GLOBAL_TICKER_LIST)
		ticker_len_text = wx.StaticText(self, -1, 
							 "Tickers = %d" % ticker_len, 
							 (10,30)
							 )
		scrape_time_secs = (ticker_len/SCRAPE_CHUNK_LENGTH) * sleep_time * 2
		scrape_time = time_from_epoch(scrape_time_secs)
		scrape_time_text = wx.StaticText(self, -1, 
					 "Time = %s" % scrape_time, 
					 (10,50)
					 )
		self.numScrapedStocks = 0

		#self.Show()
	def confirmScrape(self, event):
		confirm = wx.MessageDialog(None, 
								   "You are about to scrape of Yahoo's YQL database. If you do this too often Yahoo may temporarily block your IP address.", 
								   'Scrape stock data?', 
								   style = wx.YES_NO
								   )
		confirm.SetYesNoLabels(("&Scrape"), ("&Cancel"))
		yesNoAnswer = confirm.ShowModal()
		#try:
		#	confirm.SetYesNoLabels(("&Scrape"), ("&Cancel"))
		#except AttributeError:
		#	pass
		confirm.Destroy()

		if yesNoAnswer == wx.ID_YES:
			self.setUpScrape()

	def setUpScrape(self):
		global GLOBAL_TICKER_LIST
		global GLOBAL_STOCK_LIST
		global SCRAPE_CHUNK_LENGTH
		global SCRAPE_SLEEP_TIME
		global TIME_ALLOWED_FOR_BEFORE_RECENT_UPDATE_IS_STALE
		chunk_length = SCRAPE_CHUNK_LENGTH # 145 appears to be the longest url string i can query with
		ticker_list = []
		for ticker in GLOBAL_TICKER_LIST:
			stock = return_stock_by_symbol(ticker)
			if stock:
				time_since_update = float(time.time()) - stock.epoch
				if int(time_since_update) < int(TIME_ALLOWED_FOR_BEFORE_RECENT_UPDATE_IS_STALE):
					logging.warning("Will not add %s to update list, updated too recently, waste of yql query" % str(stock.symbol))
					continue
			ticker_list.append(ticker)
		num_of_tickers = len(ticker_list)
		sleep_time = SCRAPE_SLEEP_TIME

		# self.progress_bar.SetValue(0)
		# self.progress_bar.Show()
		# global app
		# app.Yield() # this updates the gui within a script (it must be here, or the progress bar will not show till the function finishes, also below for updates)

		slice_start = 0
		slice_end = chunk_length
		# this is a very important number
		# approx 200 calls per hour (yql forums info)
		# 3600 seconds in an hour
		# 3600 / 200 = 18 seconds pause per query to stay under the 200/hour limit
		if chunk_length < 1:
			logging.error("chunk_length too small, will create infinite loop")
			return
		count = 0
		last_loop = False

		chunk_list = []
		while slice_end < (num_of_tickers + (chunk_length)):
			if slice_end > num_of_tickers:
				slice_end = num_of_tickers
				last_loop = True
			data = None
			data2= None
			logging.info('While loop #%d' % count)
			ticker_chunk = ticker_list[slice_start:slice_end]
			chunk_list.append(ticker_chunk)
			count += 1
			print line_number(), count
			slice_start += chunk_length
			slice_end += chunk_length

		print line_number(), "got this far"
		
		#self.progress_dialog = wx.ProgressDialog('Scrape Progress', 
		#									'The stocks are currently downloading', 
		#									num_of_tickers,
		#									parent=self, 
		#									style=wx.PD_CAN_ABORT|wx.PD_REMAINING_TIME
		#									)


		number_of_tickers_in_chunk_list = 0
		for chunk in chunk_list:
			for ticker in chunk:
				number_of_tickers_in_chunk_list += 1
				print line_number(), number_of_tickers_in_chunk_list
		number_of_tickers_previously_updated = len(GLOBAL_TICKER_LIST) - number_of_tickers_in_chunk_list
		print line_number(), number_of_tickers_previously_updated
		total_number_of_tickers_done = number_of_tickers_previously_updated
		percent_of_full_scrape_done = round(100 * float(total_number_of_tickers_done) / float(len(GLOBAL_TICKER_LIST)) )

		print line_number(), percent_of_full_scrape_done
		
		self.progress_bar.SetValue(percent_of_full_scrape_done)
		self.progress_bar.Show()
		self.scrape_button.Hide()
		self.abort_scrape_button.Show()
		# Process the scrape while updating a progress bar
		timer = threading.Timer(0, self.executeScrapePartOne, [chunk_list, 0])
		timer.start()

			#scrape_thread = threading.Thread(target=self.executeOneScrape, args = (ticker_chunk,))
			#scrape_thread.daemon = True
			#scrape_thread.start()
			#while scrape_thread.isAlive():

			#	# Every two sleep times execute a new scrape
			#	full_scrape_sleep = float(sleep_time * 2)
			#	scrape_thread.join(full_scrape_sleep)
			#	cont, skip = progress_dialog.Update(self.numScrapedStocks)
			#	if not cont:
			#		progress_dialog.Destroy()
			#		return

	def executeScrapePartOne(self, ticker_chunk_list, position_of_this_chunk):
		if self.abort_scrape == True:
			self.abort_scrape = False
			self.progress_bar.Hide()
			print line_number(), "Scrape canceled."
			return
		global GLOBAL_TICKER_LIST
		global GLOBAL_STOCK_LIST
		global SCRAPE_CHUNK_LENGTH
		global SCRAPE_SLEEP_TIME
		global TIME_ALLOWED_FOR_BEFORE_RECENT_UPDATE_IS_STALE
		sleep_time = SCRAPE_SLEEP_TIME


		ticker_chunk = ticker_chunk_list[position_of_this_chunk]

		if ticker_chunk:
			scrape_1_failed = False
			try:
				data = pyql.lookupQuote(ticker_chunk)
			except:
				logging.warning("Scrape didn't work. Nothing scraped.")
				scrape_1_failed = True
			if scrape_1_failed:
				#time.sleep(sleep_time)
				return
			else:
				logging.warning("Scrape 1 Success: mid-scrape sleep for %d seconds" % sleep_time)

				timer = threading.Timer(sleep_time, self.executeScrapePartTwo, [ticker_chunk_list, position_of_this_chunk, data])
				timer.start()

	def executeScrapePartTwo(self, ticker_chunk_list, position_of_this_chunk, successful_pyql_data):
		if self.abort_scrape == True:
			self.abort_scrape = False
			self.progress_bar.Hide()
			print line_number(), "Scrape canceled."
			return
		global GLOBAL_TICKER_LIST
		global GLOBAL_STOCK_LIST
		global SCRAPE_CHUNK_LENGTH
		global SCRAPE_SLEEP_TIME
		global TIME_ALLOWED_FOR_BEFORE_RECENT_UPDATE_IS_STALE
		sleep_time = SCRAPE_SLEEP_TIME

		ticker_chunk = ticker_chunk_list[position_of_this_chunk]
		number_of_stocks_in_this_scrape = len(ticker_chunk)

		data = successful_pyql_data

		try:
			data2 = pyql.lookupKeyStats(ticker_chunk)
		except:
			logging.warning("Scrape 2 didn't work. Abort.")
			time.sleep(sleep_time)
			return

		for stock in data:
			new_stock = None
			for key, value in stock.iteritems():
				if key == "symbol":
					new_stock = return_stock_by_symbol(value)
					if not new_stock:
						new_stock = Stock(value)
						GLOBAL_STOCK_LIST.append(new_stock)
					else:
						new_stock.updated = datetime.datetime.now()
						new_stock.epoch = float(time.time())
			for key, value in stock.iteritems():
				# Here we hijack the power of the expando db structure
				# This adds the attribute of every possible attribute that can be passed
				setattr(new_stock, 
						str(key), 
						value
						)
			logging.warning("Success, putting %s: Data 1" % new_stock.symbol)
		#save
		with open('all_stocks.pk', 'wb') as output:
			pickle.dump(GLOBAL_STOCK_LIST, output, pickle.HIGHEST_PROTOCOL)		

		for stock2 in data2:
			for key, value in stock2.iteritems():
				if key == "symbol":
					new_stock = return_stock_by_symbol(value)
					if not new_stock:
						new_stock = Stock(value)
						GLOBAL_STOCK_LIST.append(new_stock)
			for key, value in stock2.iteritems():
				if isinstance(value, (list, dict)):
					#logging.warning(type(value))
					x = repr(value)
					term = None
					content = None
					#logging.warning(x)
					if x[0] == "[":
						y = ast.literal_eval(x)
						#logging.warning(y)
						for i in y:
							try:
								test = i["term"]
								test = i["content"]
							except Exception, e:
								#logging.error(new_stock.symbol)
								#logging.error(y)
								#logging.error("Seems to be [Trailing Annual Dividend Yield, Trailing Annual Dividend Yield%]")									
								continue
							#logging.warning(i)
							try:
								key_str = str(key)
								term = str(i["term"])
								term = term.replace(" ", "_")
								term = term.replace(",", "")
								term = strip_string_whitespace(term)
								key_term = key_str + "_" + term
								key_term = strip_string_whitespace(key_term)
								if "p_52_WeekHigh" in key_term:
									date = key_term[14:]
									setattr(new_stock, 
										"52_WeekHigh_Date", 
										date
										)
									key_str = "52_WeekHigh"
								elif "p_52_WeekLow" in key_term:
									date = key_term[13:]
									setattr(new_stock, 
										"52_WeekLow_Date", 
										date
										)
									key_str = "52_WeekLow"
								elif "ForwardPE_fye" in key_term:
									date = key_term[14:]
									setattr(new_stock, 
										"ForwardPE_fiscal_y_end_Date", 
										date
										)
									key_str = "ForwardPE"
								elif "EnterpriseValue_" in key_term:
									date = key_term[16:]
									setattr(new_stock, 
										"EnterpriseValue_Date", 
										date
										)
									key_str = "EnterpriseValue"
								elif "TrailingPE_ttm_" in key_term:
									date = key_term[15:] # will be of form  TrailingPE_ttm__intraday 
									setattr(new_stock, 
										"TrailingPE_ttm_Date", 
										date
										)
									key_str = "TrailingPE_ttm"
								elif "SharesShort_as_of" in key_term:
									date = key_term[18:] # will be of form SharesShort_as_of_Jul_15__2013 
									setattr(new_stock, 
										"SharesShort_as_of_Date", 
										date
										)
									key_str = "SharesShort"
								elif "ShortRatio_as_of" in key_term:
									date = key_term[16:] # will be of form SharesShort_as_of_Jul_15__2013 
									setattr(new_stock, 
										"ShortRatio_as_of_Date", 
										date
										)
									key_str = "ShortRatio"
								elif "ShortPercentageofFloat_as_of" in key_term:
									date = key_term[29:]
									setattr(new_stock, 
										"ShortPercentageofFloat_as_of_Date", 
										date
										)
									key_str = "ShortPercentageofFloat"
								elif "p_2" in key_term or "p_5" in key_term:
									key_str = key_str[2:]
								else:
									key_str = str(key + "_" + term)
								content = str(i["content"])
								setattr(new_stock, 
										key_str, 
										content
										)
							except Exception, e:
								logging.warning(repr(i))
								logging.warning("complex list method did not work")
								logging.exception(e)
								setattr(new_stock, 
										str(key), 
										x
										)

					elif x[0] == "{":
						y = ast.literal_eval(x)
						try:
							test = y["term"]
							test = y["content"]
						except Exception, e:
							#logging.error(new_stock.symbol)
							#logging.error(y)
							#logging.error("Seems to be [Trailing Annual Dividend Yield, Trailing Annual Dividend Yield%]")									
							continue
						#logging.warning(y)
						try:
							key_str = str(key)
							term = str(y["term"])
							term = term.replace(" ", "_")
							term = term.replace(",", "")
							term = strip_string_whitespace(term)
							key_term = key_str + "_" + term
							key_term = strip_string_whitespace(key_term)
							if "p_52_WeekHigh" in key_term:
								date = key_term[14:]
								setattr(new_stock, 
									"52_WeekHigh_Date", 
									date
									)
								key_str = "52_WeekHigh"
							elif "p_52_WeekLow" in key_term:
								date = key_term[13:]
								setattr(new_stock, 
									"52_WeekLow_Date", 
									date
									)
								key_str = "52_WeekLow"
							elif "ForwardPE_fye" in key_term:
								date = key_term[14:]
								setattr(new_stock, 
									"ForwardPE_fiscal_y_end_Date", 
									date
									)
								key_str = "ForwardPE"
							elif "EnterpriseValue_" in key_term:
								date = key_term[16:]
								setattr(new_stock, 
									"EnterpriseValue_Date", 
									date
									)
								key_str = "EnterpriseValue"
							elif "TrailingPE_ttm_" in key_term:
								date = key_term[15:] # will be of form  TrailingPE_ttm__intraday 
								setattr(new_stock, 
									"TrailingPE_ttm_Date", 
									date
									)
								key_str = "TrailingPE_ttm"
							elif "SharesShort_as_of" in key_term:
								date = key_term[18:] # will be of form SharesShort_as_of_Jul_15__2013 
								setattr(new_stock, 
									"SharesShort_as_of_Date", 
									date
									)
								key_str = "SharesShort"
							elif "ShortRatio_as_of" in key_term:
								date = key_term[16:] # will be of form SharesShort_as_of_Jul_15__2013 
								setattr(new_stock, 
									"ShortRatio_as_of_Date", 
									date
									)
								key_str = "ShortRatio"
							elif "ShortPercentageofFloat_as_of" in key_term:
								date = key_term[29:]
								setattr(new_stock, 
									"ShortPercentageofFloat_as_of_Date", 
									date
									)
								key_str = "ShortPercentageofFloat"
							elif "p_2" in key_term or "p_5" in key_term:
								key_str = key_str[2:]
							else:
								key_str = str(key + "_" + term)
							content = str(y["content"])
							setattr(new_stock, 
									key_str, 
									content
									)
						except Exception, e:
							logging.warning("complex dict method did not work")
							logging.exception(e)
							setattr(new_stock, 
									str(key), 
									x
									)
					else:
						key_str = str(key)
						if "p_2" in key_str or "p_5" in key_str:
							key_str = key_str[2:]
						setattr(new_stock, 
							key_str, 
							x
							)
				else:
					key_str = str(key)
					if "p_2" in key_str or "p_5" in key_str:
						key_str = key_str[2:]
					setattr(new_stock, 
							key_str, 
							value
							)
			logging.warning("Success, putting %s: Data 2" % new_stock.symbol)

		#save again
		with open('all_stocks.pk', 'wb') as output:
			pickle.dump(GLOBAL_STOCK_LIST, output, pickle.HIGHEST_PROTOCOL)		

		logging.warning("This stock chunk finished successfully.")
		#self.progress_bar.SetValue((float(slice_end)/float(num_of_tickers)) * 100)
		#app.Yield()

		logging.warning("Sleeping for %d seconds before the next task" % sleep_time)
		#time.sleep(sleep_time)

		#self.numScrapedStocks += number_of_stocks_in_this_scrape
		#cont, skip = self.progress_dialog.Update(self.numScrapedStocks)
		#if not cont:
		#	self.progress_dialog.Destroy()
		#	return


		number_of_tickers_in_chunk_list = 0
		for chunk in ticker_chunk_list:
			for ticker in chunk:
				number_of_tickers_in_chunk_list += 1
		number_of_tickers_previously_updated = len(GLOBAL_TICKER_LIST) - number_of_tickers_in_chunk_list
		number_of_tickers_done_in_this_scrape = 0
		for i in range(len(ticker_chunk_list)):
			if i > position_of_this_chunk:
				continue
			for ticker in ticker_chunk_list[i]:
				number_of_tickers_done_in_this_scrape += 1
		total_number_of_tickers_done = number_of_tickers_previously_updated + number_of_tickers_done_in_this_scrape
		percent_of_full_scrape_done = round( 100 * float(total_number_of_tickers_done) / float(len(GLOBAL_TICKER_LIST)))

		position_of_this_chunk += 1
		percent_done = round( 100 * float(position_of_this_chunk) / float(len(ticker_chunk_list)) )
		print line_number(), "%d%%" % percent_done, "done this scrape execution."
		print line_number(), "%d%%" % percent_of_full_scrape_done, "done of all tickers."
		self.progress_bar.SetValue(percent_of_full_scrape_done)
		if position_of_this_chunk >= len(ticker_chunk_list):
			# finished
			self.abort_scrape_button.Hide()
			self.scrape_button.Show()
			self.progress_bar.SetValue(100)
			return
		else:
			timer = threading.Timer(sleep_time, self.executeScrapePartOne, [ticker_chunk_list, position_of_this_chunk])
			timer.start()

	def abortScrape(self, event):
		if self.abort_scrape == False:
			self.abort_scrape = True
			self.abort_scrape_button.Hide()
			self.scrape_button.Show()
class AllStocksPage(Tab):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)
		welcome_page_text = wx.StaticText(self, -1, 
							 "Full Stock List", 
							 (10,10)
							 )

		self.spreadsheet = None

		refresh_button = wx.Button(self, label="refresh", pos=(110,4), size=(-1,-1))
		refresh_button.Bind(wx.EVT_BUTTON, self.spreadSheetFill, refresh_button)

		#self.spreadSheetFill('event')

	def spreadSheetFill(self, event):
		try:
			self.spreadsheet.Destroy()
		except Exception, exception:
			print line_number(), exception

		global GLOBAL_STOCK_LIST
		stock_list = GLOBAL_STOCK_LIST
		self.spreadsheet = GridAllStocks(self, -1, size=(1000,680), pos=(0,50))


		self.spreadsheet.CreateGrid(self.spreadsheet.num_rows, self.spreadsheet.num_columns)
		self.spreadsheet.EnableEditing(False)

		attribute_list = []
		for stock in stock_list:
			for attribute in dir(stock):
				if not attribute.startswith('_'):
					attribute_list.append(str(attribute))
			break
		attribute_list.sort()
		# adjust list order for important terms
		try:
			attribute_list.insert(0, attribute_list.pop(attribute_list.index('symbol')))
		except Exception, e:
			print line_number(), e
		try:
			attribute_list.insert(1, attribute_list.pop(attribute_list.index('Name')))
		except Exception, e:
			print line_number(), e
		#print line_number(), attribute_list

		row_count = 0
		col_count = 0

		for stock in stock_list:
			for attribute in attribute_list:
				#if not attribute.startswith('_'):
				if row_count == 0:
					self.spreadsheet.SetColLabelValue(col_count, str(attribute))
				try:
					self.spreadsheet.SetCellValue(row_count, col_count, str(getattr(stock, attribute)))
				except:
					pass
				col_count += 1
			row_count += 1
			col_count = 0
		self.spreadsheet.AutoSizeColumns()
class ScreenPage(Tab):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)
		welcome_page_text = wx.StaticText(self, -1, 
							 "Screen Stocks", 
							 (10,10)
							 )
		screen_button = wx.Button(self, label="screen", pos=(110,4), size=(-1,-1))
		screen_button.Bind(wx.EVT_BUTTON, self.screenStocks, screen_button)

		self.drop_down = wx.ComboBox(self, pos=(210, 6), choices=['PE < 10', 'are','default','choices'])

		self.save_screen_button = wx.Button(self, label="save", pos=(900,4), size=(-1,-1))
		self.save_screen_button.Bind(wx.EVT_BUTTON, self.saveScreen, self.save_screen_button)
		self.save_screen_button.Hide()

		#self.my_text = wx.StaticText(self, -1, "default", (600, 10), style=wx.ALIGN_CENTRE)

		self.screen_grid = None

	def saveScreen(self, event):
		global SCREEN_LIST
		current_screen_list = SCREEN_LIST

		try:
			existing_screen_names_file = open('screen_names.pk', 'rb')
		except Exception, exception:
			print line_number(), exception
			existing_screen_names_file = open('screen_names.pk', 'wb')
			empty_list = []
			with open('screen_names.pk', 'wb') as output:
				pickle.dump(empty_list, output, pickle.HIGHEST_PROTOCOL)
			existing_screen_names_file = open('screen_names.pk', 'rb')
		existing_screen_names = pickle.load(existing_screen_names_file)

		save_popup = wx.TextEntryDialog(None,
										  "What would you like to name this group?", 
										  "Save Screen", 
										  "%s screen saved at %s" % (str(time.strftime("%Y-%m-%d")),str(time.strftime("%H:%M:%S")))
										 )
		if save_popup.ShowModal() == wx.ID_OK:
			saved_screen_name = str(save_popup.GetValue())

			if saved_screen_name in existing_screen_names:
				error = wx.MessageDialog(self,
										 'Each saved screen must have a unique name. Please try saving again with a different name.',
										 'Error: Could not save',
										 style = wx.ICON_ERROR
										 )
				error.ShowModal()
				error.Destroy()
				return
			else:
				existing_screen_names.append(saved_screen_name)
				print line_number(), existing_screen_names
				with open('screen_names.pk', 'wb') as output:
					pickle.dump(existing_screen_names, output, pickle.HIGHEST_PROTOCOL)

				with open('screen-%s.pk' % saved_screen_name, 'wb') as output:
					pickle.dump(current_screen_list, output, pickle.HIGHEST_PROTOCOL)

				self.save_screen_button.Hide()

		save_popup.Destroy()



	def screenStocks(self, event):
		global GLOBAL_STOCK_LIST
		stock_list = GLOBAL_STOCK_LIST
		drop_down_value = self.drop_down.GetValue()

		if drop_down_value == 'PE < 10':
			stock_list = screen_pe_less_than_10()

		global SCREEN_LIST
		SCREEN_LIST = stock_list

		try:
			self.screen_grid.Destroy()
		except Exception, e:
			print line_number(), e

		self.screen_grid = StockScreenGrid(self, -1, size=(1000,680), pos=(0,50))
		self.spreadSheetFill(self.screen_grid, stock_list)

		self.save_screen_button.Show()

	def spreadSheetFill(self, spreadsheet, stock_list):
		spreadsheet.CreateGrid(spreadsheet.num_rows, spreadsheet.num_columns)
		spreadsheet.EnableEditing(False)

		attribute_list = []
		for stock in stock_list:
			for attribute in dir(stock):
				if not attribute.startswith('_'):
					attribute_list.append(str(attribute))
			break
		if not attribute_list:
			return
		attribute_list.sort()
		# adjust list order for important terms
		attribute_list.insert(0, attribute_list.pop(attribute_list.index('symbol')))
		attribute_list.insert(1, attribute_list.pop(attribute_list.index('Name')))
		#print line_number(), attribute_list

		row_count = 0
		col_count = 0

		for stock in stock_list:
			for attribute in attribute_list:
				#if not attribute.startswith('_'):
				if row_count == 0:
					spreadsheet.SetColLabelValue(col_count, str(attribute))
				try:
					spreadsheet.SetCellValue(row_count, col_count, str(getattr(stock, attribute)))
				except:
					pass
				col_count += 1
			row_count += 1
			col_count = 0
		spreadsheet.AutoSizeColumns()
class SavedScreenPage(Tab):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)
		welcome_page_text = wx.StaticText(self, -1, 
							 "Saved screens", 
							 (10,10)
							 )
		refresh_screen_button = wx.Button(self, label="refresh list", pos=(110,5), size=(-1,-1))
		refresh_screen_button.Bind(wx.EVT_BUTTON, self.refreshScreens, refresh_screen_button)

		load_screen_button = wx.Button(self, label="load screen", pos=(200,5), size=(-1,-1))
		load_screen_button.Bind(wx.EVT_BUTTON, self.loadScreen, load_screen_button)

		try:
			existing_screen_names_file = open('screen_names.pk', 'rb')
		except Exception, exception:
			print line_number(), exception
			existing_screen_names_file = open('screen_names.pk', 'wb')
			empty_list = []
			with open('screen_names.pk', 'wb') as output:
				pickle.dump(empty_list, output, pickle.HIGHEST_PROTOCOL)
			existing_screen_names_file = open('screen_names.pk', 'rb')
		existing_screen_names = pickle.load(existing_screen_names_file)
		existing_screen_names_file.close()
		self.drop_down = wx.ComboBox(self, 
									 pos=(305, 6), 
									 choices=existing_screen_names,
									 style = wx.TE_READONLY
									 )

		self.currently_viewed_screen = None
		self.delete_screen_button = wx.Button(self, label="delete", pos=(900,4), size=(-1,-1))
		self.delete_screen_button.Bind(wx.EVT_BUTTON, self.deleteScreen, self.delete_screen_button)
		self.delete_screen_button.Hide()
		
		self.screen_grid = None

	def deleteScreen(self, event):
		confirm = wx.MessageDialog(None, 
								   "You are about to delete this screen.", 
								   'Are you sure?', 
								   wx.YES_NO
								   )
		confirm.SetYesNoLabels(("&Delete"), ("&Cancel"))
		yesNoAnswer = confirm.ShowModal()
		confirm.Destroy()


		print line_number(), self.screen_grid
		if yesNoAnswer != wx.ID_YES:
			return
		try:
			print line_number(), self.currently_viewed_screen
			existing_screen_names_file = open('screen_names.pk', 'rb')
			existing_screen_names = pickle.load(existing_screen_names_file)
			#print line_number(), existing_screen_names
			existing_screen_names.remove(self.currently_viewed_screen)
			with open('screen_names.pk', 'wb') as output:
				pickle.dump(existing_screen_names, output, pickle.HIGHEST_PROTOCOL)
			os.remove('screen-%s.pk' % self.currently_viewed_screen)
			self.screen_grid.Destroy()
		except Exception, exception:
			print line_number(), exception
			error = wx.MessageDialog(self,
									 "Something went wrong. File was not deleted, because this file doesn't seem to exist.",
									 'Error: File Does Not Exist',
									 style = wx.ICON_ERROR
									 )
			error.ShowModal()
			error.Destroy()
			return
		self.refreshScreens('event')

	def refreshScreens(self, event):
		self.drop_down.Hide()
		self.drop_down.Destroy()

		time.sleep(2)

		try:
			existing_screen_names_file = open('screen_names.pk', 'rb')
		except Exception, exception:
			print line_number(), exception
			existing_screen_names_file = open('screen_names.pk', 'wb')
			empty_list = []
			with open('screen_names.pk', 'wb') as output:
				pickle.dump(empty_list, output, pickle.HIGHEST_PROTOCOL)
			existing_screen_names_file = open('screen_names.pk', 'rb')
		existing_screen_names = pickle.load(existing_screen_names_file)

		self.drop_down = wx.ComboBox(self, 
									 pos=(305, 6), 
									 choices=existing_screen_names,
									 style = wx.TE_READONLY
									 )

	def loadScreen(self, event):
		selected_screen_name = self.drop_down.GetValue()
		try:
			saved_screen_file = open('screen-%s.pk' % selected_screen_name, 'rb')
			saved_screen = pickle.load(saved_screen_file)
			saved_screen_file.close()
		except Exception, exception:
			print line_number(), exception
			error = wx.MessageDialog(self,
									 "Something went wrong. This file doesn't seem to exist.",
									 'Error: File Does Not Exist',
									 style = wx.ICON_ERROR
									 )
			error.ShowModal()
			error.Destroy()
			return

		self.currently_viewed_screen = selected_screen_name
		stock_list = saved_screen

		try:
			self.screen_grid.Destroy()
		except Exception, exception:
			print line_number(), exception

		self.spreadSheetFill(stock_list)

	def spreadSheetFill(self, stock_list):
		num_rows = len(stock_list)
		num_columns = 0
		for stock in stock_list:
			num_attributes = 0
			for attribute in dir(stock):
				if not attribute.startswith('_'):
					num_attributes += 1
			if num_columns < num_attributes:
				num_columns = num_attributes
		self.screen_grid = StockScreenGrid(self, -1, size=(980,637), pos=(0,50))

		self.screen_grid.CreateGrid(num_rows, num_columns)
		self.screen_grid.EnableEditing(False)

		attribute_list = []
		for stock in stock_list:
			for attribute in dir(stock):
				if not attribute.startswith('_'):
					attribute_list.append(str(attribute))
			break
		if not attribute_list:
			logging.warning('attribute list empty')
			return
		attribute_list.sort()
		# adjust list order for important terms
		attribute_list.insert(0, attribute_list.pop(attribute_list.index('symbol')))
		attribute_list.insert(1, attribute_list.pop(attribute_list.index('Name')))
		#print line_number(), attribute_list

		row_count = 0
		col_count = 0

		for stock in stock_list:
			for attribute in attribute_list:
				#if not attribute.startswith('_'):
				if row_count == 0:
					self.screen_grid.SetColLabelValue(col_count, str(attribute))
				try:
					self.screen_grid.SetCellValue(row_count, col_count, str(getattr(stock, attribute)))
				except:
					pass
				col_count += 1
			row_count += 1
			col_count = 0
		self.screen_grid.AutoSizeColumns()

		self.delete_screen_button.Show()
class RankPage(Tab):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)

		self.full_ticker_list = [] # this should hold all tickers in any spreadsheet displayed
		self.sorted_full_ticker_list = []


		self.lists_in_ticker_list = [] # currently unused

		self.full_attribute_list = []
		global IRRELEVANT_ATTRIBUTES
		self.irrelevant_attributes = IRRELEVANT_ATTRIBUTES

		self.held_ticker_list = []
		self.screen_ticker_list = []


		rank_page_text = wx.StaticText(self, -1, 
							 "Rank", 
							 (10,10)
							 )
		refresh_screen_button = wx.Button(self, label="refresh", pos=(110,5), size=(-1,-1))
		refresh_screen_button.Bind(wx.EVT_BUTTON, self.refreshScreens, refresh_screen_button)

		load_screen_button = wx.Button(self, label="add screen", pos=(200,5), size=(-1,-1))
		load_screen_button.Bind(wx.EVT_BUTTON, self.loadScreen, load_screen_button)

		load_portfolio_button = wx.Button(self, label="add account", pos=(191,30), size=(-1,-1))
		load_portfolio_button.Bind(wx.EVT_BUTTON, self.loadAccount, load_portfolio_button)

		update_annual_data_button = wx.Button(self, label="update annual data", pos=(5,30), size=(-1,-1))
		update_annual_data_button.Bind(wx.EVT_BUTTON, self.update_annual_data, update_annual_data_button)

		try:
			existing_screen_names_file = open('screen_names.pk', 'rb')
		except Exception, exception:
			print line_number(), exception
			existing_screen_names_file = open('screen_names.pk', 'wb')
			empty_list = []
			with open('screen_names.pk', 'wb') as output:
				pickle.dump(empty_list, output, pickle.HIGHEST_PROTOCOL)
			existing_screen_names_file = open('screen_names.pk', 'rb')
		existing_screen_names = pickle.load(existing_screen_names_file)
		existing_screen_names_file.close()
		self.drop_down = wx.ComboBox(self, 
									 pos=(305, 6), 
									 choices=existing_screen_names,
									 style = wx.TE_READONLY
									 )

		global PORTFOLIO_NAMES
		self.portfolio_name_tuple_list = []
		for i in range(len(PORTFOLIO_NAMES)):
			tuple_to_append = [PORTFOLIO_NAMES[i], (i+1)]
			self.portfolio_name_tuple_list.append(tuple_to_append)
			#print line_number(), self.portfolio_name_tuple_list

		self.accounts_drop_down = wx.ComboBox(self, 
									 pos=(305, 31), 
									 choices=PORTFOLIO_NAMES,
									 style = wx.TE_READONLY
									 )


		self.currently_viewed_screen = None
		self.clear_button = wx.Button(self, label="clear", pos=(900,4), size=(-1,-1))
		self.clear_button.Bind(wx.EVT_BUTTON, self.clearGrid, self.clear_button)
		self.clear_button.Hide()

		self.sort_button = wx.Button(self, label="Sort by:", pos=(420,30), size=(-1,-1))
		self.sort_button.Bind(wx.EVT_BUTTON, self.sortStocks, self.sort_button)
		self.sort_drop_down = wx.ComboBox(self, 
									 pos=(520, 31), 
									 choices=self.full_attribute_list,
									 style = wx.TE_READONLY
									 )
		self.sort_button.Hide()
		self.sort_drop_down.Hide()

		
		self.screen_grid = None

	def update_annual_data(self, event):
		scrape_balance_sheet_income_statement_and_cash_flow(self.full_ticker_list)
		if self.full_ticker_list:
			self.spreadSheetFill(self.full_ticker_list)

	def clearGrid(self, event):
		confirm = wx.MessageDialog(None, 
								   "You are about to clear this grid.", 
								   'Are you sure?', 
								   wx.YES_NO
								   )
		confirm.SetYesNoLabels(("&Clear"), ("&Cancel"))
		yesNoAnswer = confirm.ShowModal()
		confirm.Destroy()
		if yesNoAnswer != wx.ID_YES:
			return

		self.full_ticker_list = []
		self.sorted_full_ticker_list = []
		self.full_attribute_list = []
		self.held_ticker_list = []
		self.screen_ticker_list = []
		
		self.spreadSheetFill(self.full_ticker_list)


		self.clear_button.Hide()
		self.sort_button.Hide()
		self.sort_drop_down.Hide()

	def refreshScreens(self, event):
		self.drop_down.Hide()
		self.drop_down.Destroy()

		self.accounts_drop_down.Hide()
		self.accounts_drop_down.Destroy()

		time.sleep(2)

		try:
			existing_screen_names_file = open('screen_names.pk', 'rb')
		except Exception, exception:
			print line_number(), exception
			existing_screen_names_file = open('screen_names.pk', 'wb')
			empty_list = []
			with open('screen_names.pk', 'wb') as output:
				pickle.dump(empty_list, output, pickle.HIGHEST_PROTOCOL)
			existing_screen_names_file = open('screen_names.pk', 'rb')
		existing_screen_names = pickle.load(existing_screen_names_file)

		self.drop_down = wx.ComboBox(self, 
									 pos=(305, 6), 
									 choices=existing_screen_names,
									 style = wx.TE_READONLY
									 )

		global PORTFOLIO_NAMES
		self.portfolio_name_tuple_list = []
		for i in range(len(PORTFOLIO_NAMES)):
			tuple_to_append = [PORTFOLIO_NAMES[i], (i+1)]
			self.portfolio_name_tuple_list.append(tuple_to_append)
			print line_number(), self.portfolio_name_tuple_list

		self.accounts_drop_down = wx.ComboBox(self, 
									 pos=(305, 31), 
									 choices=PORTFOLIO_NAMES,
									 style = wx.TE_READONLY
									 )
	def loadScreen(self, event):
		selected_screen_name = self.drop_down.GetValue()
		try:
			saved_screen_file = open('screen-%s.pk' % selected_screen_name, 'rb')
			saved_screen = pickle.load(saved_screen_file)
			saved_screen_file.close()
		except Exception, exception:
			print line_number(), exception
			error = wx.MessageDialog(self,
									 "Something went wrong. This file doesn't seem to exist.",
									 'Error: File Does Not Exist',
									 style = wx.ICON_ERROR
									 )
			error.ShowModal()
			error.Destroy()
			return

		self.currently_viewed_screen = selected_screen_name
		for i in saved_screen:
			if str(i.symbol) not in self.screen_ticker_list:
				self.screen_ticker_list.append(str(i.symbol))
			if str(i.symbol) not in self.full_ticker_list:
				self.full_ticker_list.append(str(i.symbol))

		try:
			self.screen_grid.Destroy()
		except Exception, exception:
			print line_number(), exception

		self.spreadSheetFill(self.full_ticker_list)
	def loadAccount(self, event):
		selected_account_name = self.accounts_drop_down.GetValue()
		tuple_not_found = True
		for this_tuple in self.portfolio_name_tuple_list:
			if selected_account_name == this_tuple[0]:
				tuple_not_found = False
				try:
					saved_account_file = open('portfolio_%d_data.pk' % this_tuple[1], 'rb')
					saved_account = pickle.load(saved_account_file)
					saved_account_file.close()
				except Exception, exception:
					print line_number(), exception
					error = wx.MessageDialog(self,
											 "Something went wrong. This file doesn't seem to exist.",
											 'Error: File Does Not Exist',
											 style = wx.ICON_ERROR
											 )
					error.ShowModal()
					error.Destroy()
					return
		if tuple_not_found:
			error = wx.MessageDialog(self,
									 "Something went wrong. This data doesn't seem to exist.",
									 'Error: Data Does Not Exist',
									 style = wx.ICON_ERROR
									 )
			error.ShowModal()
			error.Destroy()
			return

		for stock in saved_account.stock_list:
			if str(stock.symbol) not in self.held_ticker_list:
				self.held_ticker_list.append(str(stock.symbol))
			if str(stock.symbol) not in self.full_ticker_list:
				self.full_ticker_list.append(str(stock.symbol))

		try:
			self.screen_grid.Destroy()
		except Exception, exception:
			print line_number(), exception

		self.spreadSheetFill(self.full_ticker_list)
	def spreadSheetFill(self, ticker_list):
		global GLOBAL_STOCK_LIST
		stock_list = []
		annual_data_list  = []
		for ticker in ticker_list:
			stock_absent = True
			annual_data_absent = True
			for stock in GLOBAL_STOCK_LIST:
				if str(ticker) == str(stock.symbol):
					stock_list.append(stock)
					stock_absent = False
			for annual_data in GLOBAL_ANNUAL_DATA_STOCK_LIST:
				if str(ticker) == str(annual_data.symbol):
					annual_data_list.append(annual_data)
					annual_data_absent = False

			if stock_absent:
				logging.error('Ticker "%s" does not appear to be in the GLOBAL_STOCK_LIST' % ticker)
			if annual_data_absent:
				logging.error('There does not appear to be annual data for "%s," you should update annual data' % ticker)

		self.full_attribute_list = [] # Reset root attribute list
		attribute_list = []


		num_rows = len(stock_list)
		num_columns = 0
		for stock in stock_list:
			num_attributes = 0
			for attribute in dir(stock):
				if not attribute.startswith('_'):
					if attribute not in self.irrelevant_attributes:
						num_attributes += 1
			for annual_data in annual_data_list:
				if str(stock.symbol) == str(annual_data.symbol):
					for attribute in dir(annual_data):
						if not attribute.startswith('_'):
							if attribute not in self.irrelevant_attributes:
								if not attribute[-4:-2] in ["20", "30"]: # this checks to see that only most recent annual data is shown. this hack is good for 200 years!!!
									if str(attribute) != 'symbol': # here symbol will appear twice, once for stock, and another time for annual data, in the attribute list below it will be redundant and not added, but if will here if it's not skipped
										num_attributes += 1
			if num_columns < num_attributes:
				num_columns = num_attributes
		self.screen_grid = StockScreenGrid(self, -1, size=(980,637), pos=(0,60))

		self.screen_grid.CreateGrid(num_rows, num_columns)
		self.screen_grid.EnableEditing(False)


		for stock in stock_list:
			for attribute in dir(stock):
				if not attribute.startswith('_'):
					if attribute not in self.irrelevant_attributes:
						if attribute not in attribute_list:
							attribute_list.append(str(attribute))
							if str(attribute) not in self.full_attribute_list:
								self.full_attribute_list.append(str(attribute)) # Reset root attribute list
			for annual_data in annual_data_list:
				if str(stock.symbol) == str(annual_data.symbol):
					for attribute in dir(annual_data):
						if not attribute.startswith('_'):
							if attribute not in self.irrelevant_attributes:
								if not attribute[-4:-2] in ["20", "30"]: # this checks to see that only most recent annual data is shown. this hack is good for 200 years!!!
									if attribute not in attribute_list:
										attribute_list.append(str(attribute))
										if str(attribute) not in self.full_attribute_list:
											self.full_attribute_list.append(str(attribute)) # Reset root attribute list					
					break
		#for i in self.full_attribute_list:
		#	print line_number(), i
		if not attribute_list:
			logging.warning('attribute list empty')
			return
		attribute_list.sort()
		# adjust list order for important terms
		attribute_list.insert(0, attribute_list.pop(attribute_list.index('symbol')))
		attribute_list.insert(1, attribute_list.pop(attribute_list.index('Name')))
		#print line_number(), attribute_list

		row_count = 0
		for stock in stock_list:
			col_count = 0
			stock_annual_data = return_existing_StockAnnualData(str(stock.symbol))
			for attribute in attribute_list:
				#if not attribute.startswith('_'):
				if row_count == 0:
					self.screen_grid.SetColLabelValue(col_count, str(attribute))
					#print str(attribute)
				try:
					self.screen_grid.SetCellValue(row_count, col_count, str(getattr(stock, attribute)))
					if str(stock.symbol) in self.held_ticker_list:
						self.screen_grid.SetCellBackgroundColour(row_count, col_count, "#FAEFCF")
					if str(getattr(stock, attribute)).startswith("(") or str(getattr(stock, attribute)).startswith("-"):
						self.screen_grid.SetCellTextColour(row_count, col_count, "#8A0002")
				except Exception, exception:
					try:
						self.screen_grid.SetCellValue(row_count, col_count, str(getattr(stock_annual_data, attribute)))
						if str(stock.symbol) in self.held_ticker_list:
							self.screen_grid.SetCellBackgroundColour(row_count, col_count, "#FAEFCF")
						if str(getattr(stock_annual_data, attribute)).startswith("(") or (str(getattr(stock_annual_data, attribute)).startswith("-") and len(str(getattr(stock_annual_data, attribute))) > 1):
							self.screen_grid.SetCellTextColour(row_count, col_count, "#8A0002")
					except:
						#print "No %s attribute for %s" % (str(attribute), str(stock.symbol))
						pass
					#print line_number(), exception
				# try:
				# 	if str(getattr(stock, attribute)) in ["N/A", "-", "None"]:
				# 		self.screen_grid.SetCellValue(row_count, col_count, "")
				# except:
				# 	try:
				# 		if str(getattr(stock_annual_data, attribute)) in ["N/A", "-", "None"]:
				# 			self.screen_grid.SetCellValue(row_count, col_count, "")
				# 	except Exception, exception:
				# 		pass
				col_count += 1
			row_count += 1
		#print attribute_list
		self.screen_grid.AutoSizeColumns()

		try:
			self.sort_drop_down.Destroy()
			self.sort_drop_down = wx.ComboBox(self, 
											 pos=(520, 31), 
											 choices=self.full_attribute_list,
											 style = wx.TE_READONLY
											 )
		except Exception, exception:
			pass
			#print line_number(), exception
		self.clear_button.Show()
		self.sort_button.Show()
		self.sort_drop_down.Show()
	def sortStocks(self, event):
		sort_field = self.sort_drop_down.GetValue()
		do_not_sort_reversed = ["symbol"]
		if sort_field in do_not_sort_reversed:
			reverse_var = False
		else:
			reverse_var = True

		num_stock_value_list = []
		str_stock_value_list = []
		incompatible_stock_list = []
		self.full_ticker_list = remove_list_duplicates(self.full_ticker_list)
		for ticker in self.full_ticker_list:
			stock = return_stock_by_symbol(ticker)
			if stock:
				try:
					val = getattr(stock, sort_field)
					try:
						float(val)
						num_stock_value_list.append(stock)
					except:
						str_stock_value_list.append(stock)
				except Exception, exception:
					#print line_number(), exception
					incompatible_stock_list.append(stock)

		num_stock_value_list.sort(key = lambda x: float(getattr(x, sort_field)), reverse=reverse_var)
		
		str_stock_value_list.sort(key = lambda x: getattr(x, sort_field))

		incompatible_stock_list.sort(key = lambda x: x.symbol)

		self.sorted_full_ticker_list = []
		for stock in num_stock_value_list:
			self.sorted_full_ticker_list.append(str(stock.symbol))
		for stock in str_stock_value_list:
			self.sorted_full_ticker_list.append(str(stock.symbol))
		for incompatible_stock in incompatible_stock_list:
			self.sorted_full_ticker_list.append(str(incompatible_stock.symbol))
		self.spreadSheetFill(self.sorted_full_ticker_list)
		self.sort_drop_down.SetStringSelection(sort_field)
class SalePrepPage(Tab):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)
		trade_page_text = wx.StaticText(self, -1, 
							 "Sale Prep", 
							 (10,10)
							 )
		self.ticker_list = []



		global NUMBER_OF_PORTFOLIOS
		global PORTFOLIO_NAMES

		global PORTFOLIO_OBJECTS_LIST
		self.portfolio_obj_list = PORTFOLIO_OBJECTS_LIST
		
		self.checkbox_list = []
		for i in range(NUMBER_OF_PORTFOLIOS):
			horizontal_offset = 0
			if i>=5:
				horizontal_offset = 200
			checkbox_to_add = wx.CheckBox(self, -1, 
										  PORTFOLIO_NAMES[i], 
										  pos=((600+ horizontal_offset), (16*i)), 
										  size=(-1,-1)
										  )
			try:
				throw_error = PORTFOLIO_OBJECTS_LIST[i].stock_list
				checkbox_to_add.SetValue(True)
			except Exception, exception:
				pass#print line_number(), exception
			self.checkbox_list.append(checkbox_to_add)
		
		line = wx.StaticLine(self, -1, pos=(0,83), size=(1000,-1))

		refresh_button = wx.Button(self, label="Clear and Refresh Spreadsheet", pos=(110,5), size=(-1,-1))
		refresh_button.Bind(wx.EVT_BUTTON, self.spreadSheetFill, refresh_button)

		load_new_account_data_button = wx.Button(self, label="Refresh Accounts Data and Spreadsheet", pos=(110,30), size=(-1,-1))
		load_new_account_data_button.Bind(wx.EVT_BUTTON, self.refreshAccountData, load_new_account_data_button)

		self.save_button = wx.Button(self, label="Export for Trade Window", pos=(420,50), size=(-1,-1))
		self.save_button.Bind(wx.EVT_BUTTON, self.exportSaleCandidates, self.save_button)
		self.save_button.Hide()

		self.saved_text = wx.StaticText(self, -1, 
										"Data is now in memory.", 
										(433,55)
										)
		self.saved_text.Hide()

		self.grid = None
		for i in range(len(self.checkbox_list)):
			box = self.checkbox_list[i]
			if box:
				is_checked = box.GetValue()
				#print line_number(), is_checked
				if is_checked:
					self.spreadSheetFill('event')
					break

	def exportSaleCandidates(self, event):
		self.save_button.Hide()

		num_columns = self.grid.GetNumberCols()
		num_rows = self.grid.GetNumberRows()

		global DEFAULT_ROWS_ON_SALES_PREP_PAGE
		default_rows = DEFAULT_ROWS_ON_SALES_PREP_PAGE
		
		sell_tuple_list = [] # this will end up being a list of tuples for each stock to sell
		for column_num in range(num_columns):
			for row_num in range(num_rows):
				if not row_num >= default_rows:
					continue
				elif column_num == 7:
					not_empty = self.grid.GetCellValue(row_num, column_num)
					error = self.grid.GetCellValue(row_num, column_num - 1) # error column is one less than stock column
					if error != "Error":
						error = None
					#print not_empty
					if not_empty and not error:
						ticker = str(self.grid.GetCellValue(row_num, 3))
						number_of_shares_to_sell = int(self.grid.GetCellValue(row_num, 7))
						sell_tuple = (ticker, number_of_shares_to_sell)
						sell_tuple_list.append(sell_tuple)
					elif error:
						print "ERROR: Could not save sell list. There are errors in quantity syntax."
						return

		for i in sell_tuple_list:
			print i

		# Here, i'm not sure whether to save to file or not (currently not saving to file, obviously)
		relevant_portfolios_list = []
		for i in range(len(self.checkbox_list)):
			box = self.checkbox_list[i]
			is_checked = box.GetValue()
			if is_checked:
				relevant_portfolios_list.append(self.portfolio_obj_list[i])

		global SALE_PREP_PORTFOLIOS_AND_SALE_CANDIDATES_TUPLE
		SALE_PREP_PORTFOLIOS_AND_SALE_CANDIDATES_TUPLE= [
															relevant_portfolios_list,
															sell_tuple_list
														]

		self.saved_text.Show()
		
	def refreshAccountData(self, event):
		######## Rebuild Checkbox List in case of new accounts
		global PORTFOLIO_OBJECTS_LIST
		self.portfolio_obj_list = PORTFOLIO_OBJECTS_LIST
		for i in self.checkbox_list:
			try:
				i.Destroy()
			except Exception, exception:
				print line_number(), exception
		self.checkbox_list = []
		for i in range(NUMBER_OF_PORTFOLIOS):
			horizontal_offset = 0
			if i>=5:
				horizontal_offset = 200
			checkbox_to_add = wx.CheckBox(self, -1, 
										  PORTFOLIO_NAMES[i], 
										  pos=((600 + horizontal_offset), (16*i)), 
										  size=(-1,-1)
										  )
			try:
				throw_error = PORTFOLIO_OBJECTS_LIST[i].stock_list
				checkbox_to_add.SetValue(True)
			except Exception, exception:
				pass#print line_number(), exception
			self.checkbox_list.append(checkbox_to_add)
		self.spreadSheetFill("event")

	def hideSaveButtonWhileEnteringData(self, event):
		# This function has been deactivated, unfortunately it causes too many false positives...
		
		# color = self.grid.GetCellBackgroundColour(event.GetRow(), event.GetCol())
		# print color
		# print type(color)
		# print "---------"
		# if color != (255, 255, 255, 255):
		# 	print 'it works'
		# 	self.save_button.Hide()
		# event.Skip()
		
		pass


	def spreadSheetFill(self, event):
		try:
			self.grid.Destroy()
		except Exception, exception:
			pass
			#print line_number(), exception
		
		relevant_portfolios_list = []
		for i in range(len(self.checkbox_list)):
			box = self.checkbox_list[i]
			is_checked = box.GetValue()
			if is_checked:
				relevant_portfolios_list.append(self.portfolio_obj_list[i])

		num_columns = 17
		
		global DEFAULT_ROWS_ON_SALES_PREP_PAGE
		default_rows = DEFAULT_ROWS_ON_SALES_PREP_PAGE
		
		num_rows = default_rows
		for account in relevant_portfolios_list:
			try:
				num_rows += 1 # for account name
				num_stocks = len(account.stock_list)
				num_rows += num_stocks
				#print line_number(), num_rows
			except Exception, exception:
				pass#print line_number(), exception

		self.grid = SalePrepGrid(self, -1, size=(1000,650), pos=(0,83))
		self.grid.CreateGrid(num_rows, num_columns)
		self.grid.Bind(wx.grid.EVT_GRID_CELL_CHANGE, self.updateGrid, self.grid)

		# I deactivated this binding because it caused too much confusion if you don't click on a white square after entering data
		# self.grid.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK ,self.hideSaveButtonWhileEnteringData, self.grid)



		for column_num in range(num_columns):
			for row_num in range(num_rows):
				if not ((row_num >= default_rows and column_num in [1,2]) or (row_num == 3 and column_num == 14)):
					self.grid.SetReadOnly(row_num, column_num, True)
				elif column_num == 14:
					self.grid.SetCellBackgroundColour(row_num, column_num, "#C5DBCA")
				elif column_num == 1:
					self.grid.SetCellBackgroundColour(row_num, column_num, "#CFE8FC")
				elif column_num == 2:
					self.grid.SetCellBackgroundColour(row_num, column_num, "#CFFCEF")

		self.grid.SetCellValue(2, 0, str(time.time()))
		self.grid.SetCellValue(2, 14, "Input carryover loss (if any)")
		self.grid.SetCellValue(3, 14, str(0.00))

		self.grid.SetCellValue(7, 0, "Totals:")
		
		for i in range(num_columns):
			self.grid.SetCellBackgroundColour(6, i, "#333333")
			self.grid.SetCellBackgroundColour(8, i, "#333333")


		# Note: i should define the locations on the grid, THEN attach those variables to the set cell function.

		self.grid.SetCellValue(5, 1, "# of shares to sell")
		self.grid.SetCellValue(5, 2, "% of shares to sell")
		self.grid.SetCellValue(5, 3, "Ticker")
		self.grid.SetCellValue(5, 4, "")#Syntax Check")
		self.grid.SetCellValue(5, 5, "Name")
		self.grid.SetCellValue(5, 6, "Sale Check")
		self.grid.SetCellValue(5, 7, "# of shares to sell")
		self.grid.SetCellValue(5, 8, "% of shares to sell")
		self.grid.SetCellValue(5, 9, "Total # of shares")
		self.grid.SetCellValue(5, 10, "Price")
		self.grid.SetCellValue(5, 11, "Sale Value")
		self.grid.SetCellValue(5, 12, "Commission loss ($10/trade)")
		self.grid.SetCellValue(5, 13, "FIFO Capital Gains")
		self.grid.SetCellValue(5, 14, "Adjusted Capital Gains (including carryovers)")
		self.grid.SetCellValue(5, 15, "Market Value")
		self.grid.SetCellValue(5, 16, "Unrealized Capital +/-")

		global PORTFOLIO_NAMES
		portfolio_num = 0

		row_count = default_rows
		col_count = 0
		for account in relevant_portfolios_list:
			try:
				throw_error = account.stock_list
				# intentionally throws an error if account hasn't been imported

				self.grid.SetCellValue(row_count, 0, PORTFOLIO_NAMES[portfolio_num])
				self.grid.SetCellBackgroundColour(row_count, 1, "white")
				self.grid.SetReadOnly(row_count, 1, True)
				self.grid.SetCellBackgroundColour(row_count, 2, "white")
				self.grid.SetReadOnly(row_count, 2, True)
				portfolio_num += 1
				row_count += 1

				for stock in account.stock_list:
					#if row_count == 0:
					#	self.screen_grid.SetColLabelValue(col_count, str(attribute))
					stock_data = return_stock_by_symbol(stock.symbol)

					self.grid.SetCellValue(row_count, 3, stock.symbol)
					try:
						self.grid.SetCellValue(row_count, 5, stock_data.Name)
					except Exception, exception:
						print line_number(), exception
					self.grid.SetCellValue(row_count, 9, stock.quantity)
					try:
						self.grid.SetCellValue(row_count, 10, stock_data.LastTradePriceOnly)
					except Exception, exception:
						print line_number(), exception
					self.grid.SetCellValue(row_count, 15, str(float(stock.quantity.replace(",","")) * float(stock_data.LastTradePriceOnly)))
					row_count += 1
			except Exception, exception:
				print line_number(), exception, "\nAn account appears to not be loaded with a .csv, but this isn't a problem."
		self.grid.AutoSizeColumns()
	def updateGrid(self, event):
		row = event.GetRow()
		column = event.GetCol()
		value = self.grid.GetCellValue(row, column)
		num_shares = str(self.grid.GetCellValue(row, 9))
		num_shares = num_shares.replace(",","")
		value = strip_string_whitespace(value)
		price = self.grid.GetCellValue(row, 10)
		if column == 1:
			try:
				number_of_shares_to_sell = int(value)
			except Exception, exception:
				print line_number(), exception
				number_of_shares_to_sell = None
				#self.setGridError(row) # this should actually be changed below
			#print line_number(), "# of stocks to sell changed"
			self.grid.SetCellValue(row, 2, "")
			if str(number_of_shares_to_sell).isdigit() and num_shares >= number_of_shares_to_sell and number_of_shares_to_sell != 0:
				self.grid.SetCellValue(row, 7, str(number_of_shares_to_sell))
				percent_of_total_holdings = round(100 * float(number_of_shares_to_sell)/float(num_shares))
				self.grid.SetCellValue(row, 8, "%d%%" % percent_of_total_holdings)
				if int(num_shares) == int(number_of_shares_to_sell):
					self.grid.SetCellValue(row, 6, "All")
					self.grid.SetCellTextColour(row, 6, "black")
				else:
					self.grid.SetCellValue(row, 6, "Some")
					self.grid.SetCellTextColour(row, 6, "black")
				sale_value = float(number_of_shares_to_sell) * float(price)
				self.grid.SetCellValue(row, 11, "$%.2f" % sale_value)

				percent_to_commission = 100 * 10/sale_value
				self.grid.SetCellValue(row, 12, "%.2f%%" % percent_to_commission)

			elif value == "" or number_of_shares_to_sell == 0:
				self.grid.SetCellValue(row, 7, "")
				self.grid.SetCellValue(row, 8, "")
				self.grid.SetCellValue(row, 6, "")
				self.grid.SetCellTextColour(row, 6, "black")

			else:
				self.setGridError(row)

		if column == 2:
			if "%" in value:
				value = value.strip("%")
				try:
					value = float(value)/100
				except Exception, exception:
					print line_number(), exception
					self.setGridError(row)
					return
			else:
				try:
					value = float(value)
				except Exception, exception:
					print line_number(), exception
					if value != "":
						self.setGridError(row)
						return
			percent_of_holdings_to_sell = value
			self.grid.SetCellValue(row, 1, "")

			if percent_of_holdings_to_sell == "" or percent_of_holdings_to_sell == 0:
				self.grid.SetCellValue(row, 7, "")
				self.grid.SetCellValue(row, 8, "")
				self.grid.SetCellValue(row, 6, "")
				self.grid.SetCellTextColour(row, 6, "black")

			elif percent_of_holdings_to_sell <= 1:
				self.grid.SetCellValue(row, 8, "%d%%" % round(percent_of_holdings_to_sell * 100))

				number_of_shares_to_sell = int(math.floor( int(num_shares) * percent_of_holdings_to_sell ) )
				self.grid.SetCellValue(row, 7, str(number_of_shares_to_sell))

				if int(num_shares) == int(number_of_shares_to_sell):
					self.grid.SetCellValue(row, 6, "All")
					self.grid.SetCellTextColour(row, 6, "black")
				else:
					self.grid.SetCellValue(row, 6, "Some")
					self.grid.SetCellTextColour(row, 6, "black")
				sale_value = float(number_of_shares_to_sell) * float(price)
				self.grid.SetCellValue(row, 11, "$%.2f" % sale_value)

				percent_to_commission = 100 * 10/sale_value
				self.grid.SetCellValue(row, 12, "%.2f%%" % percent_to_commission)



			else:
				self.setGridError(row)
		self.saved_text.Hide()
		self.save_button.Show()
		#print "Show Me!"

	def setGridError(self, row):
		self.grid.SetCellValue(row, 6, "Error")
		self.grid.SetCellTextColour(row, 6, "red")

		self.grid.SetCellValue(row, 7, "")
		self.grid.SetCellValue(row, 8, "")
		self.grid.SetCellValue(row, 11, "")
		self.grid.SetCellValue(row, 12, "")
class TradePage(Tab):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)
		trade_page_text = wx.StaticText(self, -1, 
							 "Set up trades", 
							 (10,10)
							 )
		self.ticker_list = []
		
		self.relevant_portfolios_list = []
		self.sale_tuple_list = []

		self.default_rows_above_buy_candidates = 5
		self.default_buy_candidate_column = 7
		self.default_buy_candidate_quantity_column = 14
		self.buy_candidates = [] # this will be tickers to buy, but no quantities
		self.buy_candidate_tuples = [] # this will be tickers ROWS with quantities, if they don't appear in previous list, there will be disregarded, because data has been changed.

		self.default_columns = 19
		self.default_min_rows = 17

		import_sale_candidates_button = wx.Button(self, label="Import sale candidates and refresh spreadsheet", pos=(0,30), size=(-1,-1))
		import_sale_candidates_button.Bind(wx.EVT_BUTTON, self.importSaleCandidates, import_sale_candidates_button)

		create_grid_button = wx.Button(self, label="create grid", pos=(500,30), size=(-1,-1))
		create_grid_button.Bind(wx.EVT_BUTTON, self.makeGridOnButtonPush, create_grid_button)
		self.grid_list = []


		self.grid = None

	def importSaleCandidates(self, event):
		print "Boom goes the boom!!!!!!!!"
		global SALE_PREP_PORTFOLIOS_AND_SALE_CANDIDATES_TUPLE

		self.relevant_portfolios_list = SALE_PREP_PORTFOLIOS_AND_SALE_CANDIDATES_TUPLE[0]
		self.sale_tuple_list = SALE_PREP_PORTFOLIOS_AND_SALE_CANDIDATES_TUPLE[1]
		
		for portfolio in self.relevant_portfolios_list:
			id_number = portfolio.id_number
			print id_number
			global PORTFOLIO_NAMES
			print PORTFOLIO_NAMES[id_number - 1]
		print self.sale_tuple_list

		# Now, how to refresh only parts of the list... hmmmm
	def makeGridOnButtonPush(self, event):
		self.newGridFill()
	def spreadSheetFill(self, cursor_positon = (0,0) ):
		pass # currently redundant

		# print cursor_positon
		# try:
		# 	self.grid.Destroy()
		# 	print "Destroyed grid"
		# except Exception, exception:
		# 	#pass
		# 	print line_number(), exception

		# # CREATE A GRID HERE
		# self.grid = TradeGrid(self, -1, size=(1000,650), pos=(0,83))
		# # calc rows
		# global SALE_PREP_PORTFOLIOS_AND_SALE_CANDIDATES_TUPLE
		# global PORTFOLIO_NAMES
		# relevant_portfolio_name_list = []
		# try:
		# 	self.relevant_portfolios_list = []
		# 	for account in SALE_PREP_PORTFOLIOS_AND_SALE_CANDIDATES_TUPLE[0]:
		# 		id_number = account.id_number
		# 		self.relevant_portfolios_list.append(account)
		# 		relevant_portfolio_name_list.append(PORTFOLIO_NAMES[(id_number - 1)])

		# 	num_rows = len(SALE_PREP_PORTFOLIOS_AND_SALE_CANDIDATES_TUPLE[1])
		# 	global DEFAULT_ROWS_ON_TRADE_PREP_PAGE_FOR_TICKERS
		# 	num_rows += DEFAULT_ROWS_ON_TRADE_PREP_PAGE_FOR_TICKERS
		# except Exception, exception:
		# 	print line_number(), exception
		# 	num_rows = 0

		# num_rows = max(num_rows, self.default_min_rows, (self.default_rows_above_buy_candidates + len(self.buy_candidates) + 1))
		# self.grid.CreateGrid(num_rows, self.default_columns)
		# self.grid.Bind(wx.grid.EVT_GRID_CELL_CHANGE, self.updateGrid, self.grid)

		# for column_num in range(self.default_columns):
		# 	for row_num in range(num_rows):
		# 		if row_num <= self.default_rows_above_buy_candidates or row_num > (self.default_rows_above_buy_candidates + len(self.buy_candidates) + 1) or column_num not in [self.default_buy_candidate_column,14]:
		# 			self.grid.SetReadOnly(row_num, column_num, True)
		# 		elif column_num == self.default_buy_candidate_column:
		# 			self.grid.SetCellBackgroundColour(row_num, column_num, "#FAEFCF")
		# 		elif column_num == 14:
		# 			self.grid.SetCellBackgroundColour(row_num, column_num, "#CFE8FC")


		# # Defining cells separately from forming them so they are easy to edit
		# # e.g. dummy_cell_var = [Row, Column, "Name/Value"]
		# # cell_list = [dummy_cell_var, dummy_cell_2, etc...]
		# # for cell in cell_list:
		# # 	self.grid.SetCellValue(cell[0],cell[1],cell[2])
		# spreadsheet_cell_list = []

		# # Start with static values (large if statement for code folding purposes only)
		# if "This section sets the static cell values by column" == "This section sets the static cell values by column":
		# 	# Column 0 (using zero-based numbering for simplicity):
		# 	this_column_number = 0

		# 	title_with_relevant_portfolios_string = "Trade Prep (" + ", ".join(relevant_portfolio_name_list) + ")"

		# 	name_of_spreadsheet_cell = [0, this_column_number, title_with_relevant_portfolios_string]
		# 	share_to_sell_cell = [2, this_column_number, "Shares to sell:"]
		# 	ticker_title_cell = [3, this_column_number, "Ticker"]

		# 	spreadsheet_cell_list.append(name_of_spreadsheet_cell)
		# 	spreadsheet_cell_list.append(share_to_sell_cell)
		# 	spreadsheet_cell_list.append(ticker_title_cell)

		# 	# Column 1:
		# 	this_column_number = 1

		# 	num_shares_cell = [3, this_column_number,"# shares"]		
		# 	spreadsheet_cell_list.append(num_shares_cell)

		# 	# Column 2:
		# 	this_column_number = 2

		# 	volume_title_cell = [3, this_column_number, "Volume"]
		# 	spreadsheet_cell_list.append(volume_title_cell)

		# 	# Column 3:
		# 	# empty

		# 	# Column 4:
		# 	this_column_number = 4

		# 	total_asset_cell = [0, this_column_number, "Total asset value ="]
		# 	approximate_surplus_cash_cell = [3, this_column_number, "Approximate surplus cash from sale ="]
		# 	percent_total_cash_cell = [6, this_column_number, "%% Total Cash After Sale"]
		# 	portfolio_cash_available_cell = [9, this_column_number, "Portfolio Cash Available ="]
		# 	num_stocks_to_look_cell = [12, this_column_number, "# of stocks to look at at for 3%% of portfolio each."]
		# 	approximate_to_spend_cell = [15, this_column_number, "Approximate to spend on each (3%) stock."]

		# 	spreadsheet_cell_list.append(total_asset_cell)
		# 	spreadsheet_cell_list.append(approximate_surplus_cash_cell)
		# 	spreadsheet_cell_list.append(percent_total_cash_cell)
		# 	spreadsheet_cell_list.append(portfolio_cash_available_cell)
		# 	spreadsheet_cell_list.append(num_stocks_to_look_cell)
		# 	spreadsheet_cell_list.append(approximate_to_spend_cell)

		# 	# Column 5:
		# 	# empty

		# 	# Column 6:
		# 	this_column_number = 6

		# 	num_symbol_cell = [5, this_column_number, "#"]
		# 	spreadsheet_cell_list.append(num_symbol_cell)

		# 	# Column 7:
		# 	this_column_number = 7

		# 	shares_to_buy_cell = [2, this_column_number, "Shares to buy:"]
		# 	input_ticker_cell = [3, this_column_number, "Input ticker"]

		# 	spreadsheet_cell_list.append(shares_to_buy_cell)
		# 	spreadsheet_cell_list.append(input_ticker_cell)

		# 	# Column 8:
		# 	# empty

		# 	# Column 9:
		# 	# empty

		# 	# Column 10:
		# 	this_column_number = 10

		# 	num_shares_to_buy_cell = [2, this_column_number, "# of shares to buy for"]
		# 	three_percent_cell = [3, this_column_number, "3%"]

		# 	spreadsheet_cell_list.append(num_shares_to_buy_cell)
		# 	spreadsheet_cell_list.append(three_percent_cell)

		# 	# Column 11:
		# 	this_column_number = 11

		# 	for_cell = [2, this_column_number, "for"]
		# 	five_percent_cell = [3, this_column_number, "5%"]

		# 	spreadsheet_cell_list.append(for_cell)
		# 	spreadsheet_cell_list.append(five_percent_cell)

		# 	# Column 12:
		# 	this_column_number = 12

		# 	for_cell_2 = [2, this_column_number, "for"]
		# 	ten_percent_cell = [3, this_column_number, "10%"]

		# 	spreadsheet_cell_list.append(for_cell_2)
		# 	spreadsheet_cell_list.append(ten_percent_cell)

		# 	# Column 13:
		# 	# empty

		# 	# Column 14:
		# 	this_column_number = 14

		# 	input_num_shares_cell = [3, this_column_number, "Input # Shares to Purchase"]
		# 	spreadsheet_cell_list.append(input_num_shares_cell)

		# 	# Column 15:
		# 	this_column_number = 15

		# 	cost_cell = [3, this_column_number, "Cost"]
		# 	spreadsheet_cell_list.append(cost_cell)

		# 	# Column 16: 
		# 	# empty

		# 	# Column 17:
		# 	this_column_number = 17

		# 	total_cost_cell = [1, this_column_number, "Total Cost ="]
		# 	adjusted_cash_cell = [2, this_column_number, "Adjusted Cash Available ="]
		# 	num_stocks_to_purchase_cell = [3, this_column_number, "Number of stocks left to purchase at 3% ="]
		# 	new_cash_percentage_cell = [4, this_column_number, "New cash %% of portfolio ="]
		# 	# this cell may be irrelevant
		# 	new_cash_total_cell = [5, this_column_number, "New cash %% of total ="]

		# 	spreadsheet_cell_list.append(total_cost_cell)
		# 	spreadsheet_cell_list.append(adjusted_cash_cell)
		# 	spreadsheet_cell_list.append(num_stocks_to_purchase_cell)
		# 	spreadsheet_cell_list.append(new_cash_percentage_cell)
		# 	spreadsheet_cell_list.append(new_cash_total_cell)

		# 	# Column 18:
		# 	# computed values only

		# if "This section sets the variable cell values with relevant data" == "This section sets the variable cell values with relevant data":

		# 	# Column 0-2 data:
		# 	this_column_number = 0
		# 	default_rows = DEFAULT_ROWS_ON_TRADE_PREP_PAGE_FOR_TICKERS # called globally above
		# 	counter = 0
		# 	for stock_tuple in SALE_PREP_PORTFOLIOS_AND_SALE_CANDIDATES_TUPLE[1]:
		# 		ticker = stock_tuple[0]
		# 		number_of_shares_to_sell = stock_tuple[1]
		# 		stock = return_stock_by_symbol(ticker)
		# 		correct_row = counter + default_rows
				
		# 		ticker_cell = [correct_row, this_column_number, ticker]
		# 		number_of_shares_to_sell_cell = [correct_row, (this_column_number + 1), str(number_of_shares_to_sell)]

		# 		spreadsheet_cell_list.append(ticker_cell)
		# 		spreadsheet_cell_list.append(number_of_shares_to_sell_cell)

		# 		try:
		# 			avg_daily_volume = stock.AverageDailyVolume
		# 			volume_cell = [correct_row, (this_column_number + 2), str(avg_daily_volume)]
		# 			spreadsheet_cell_list.append(volume_cell)
		# 		except Exception, exception:
		# 			print line_number(), exception

		# 		counter += 1

		# 	# Column 4 data:
		# 	this_column_number = 4

		# 	## total asset value
		# 	total_asset_value_row = 1

		# 	total_asset_value = 0.00
		# 	for account in self.relevant_portfolios_list:
		# 		total_asset_value += float(account.availble_cash.replace("$",""))
		# 		for stock in account.stock_list:
		# 			stock_data = return_stock_by_symbol(stock.symbol)
		# 			quantity = float(stock.quantity.replace(",",""))
		# 			last_price = float(stock_data.LastTradePriceOnly)
		# 			value_of_held_stock = last_price * quantity
		# 			total_asset_value += value_of_held_stock

		# 	total_asset_value_cell = [total_asset_value_row, this_column_number, ("$" + str(total_asset_value))]
		# 	spreadsheet_cell_list.append(total_asset_value_cell)

		# 	## approximate surplus cash
		# 	approximate_surplus_cash_row = 4

		# 	value_of_all_stock_to_sell = 0.00
		# 	for stock_tuple in SALE_PREP_PORTFOLIOS_AND_SALE_CANDIDATES_TUPLE[1]:
		# 		ticker = stock_tuple[0]
		# 		number_of_shares_to_sell = int(stock_tuple[1])
		# 		stock_data = return_stock_by_symbol(ticker)
		# 		last_price = float(stock_data.LastTradePriceOnly)
		# 		value_of_single_stock_to_sell = last_price * number_of_shares_to_sell
		# 		value_of_all_stock_to_sell += value_of_single_stock_to_sell
		# 	surplus_cash_cell = [approximate_surplus_cash_row, this_column_number, ("$" + str(value_of_all_stock_to_sell))]
		# 	spreadsheet_cell_list.append(surplus_cash_cell)

		# 	## percent of portfolio that is cash after sale
		# 	percent_cash_row = 7
			
		# 	total_cash = 0.00
		# 	for account in self.relevant_portfolios_list:
		# 		total_cash += float(account.availble_cash.replace("$",""))
		# 	total_cash += value_of_all_stock_to_sell
		# 	if total_cash != 0:
		# 		percent_cash = total_cash / total_asset_value
		# 		percent_cash = round(percent_cash * 100)
		# 		percent_cash = str(percent_cash) + "%"
		# 	else:
		# 		percent_cash = "Null"

		# 	percent_cash_cell = [percent_cash_row, this_column_number, percent_cash]
		# 	spreadsheet_cell_list.append(percent_cash_cell)

		# 	## portfolio cash available after sale
		# 	cash_after_sale_row = 10

		# 	total_cash_after_sale = total_cash # from above
		# 	total_cash_after_sale = "$" + str(total_cash_after_sale)

		# 	total_cash_after_sale_cell = [cash_after_sale_row, this_column_number, total_cash_after_sale]
		# 	spreadsheet_cell_list.append(total_cash_after_sale_cell)

		# 	## Number of stocks to purchase at 3% each
		# 	stocks_at_three_percent_row = 13

		# 	three_percent_of_all_assets = 0.03 * total_asset_value # from above
		# 	try:
		# 		number_of_stocks_at_3_percent = total_cash / three_percent_of_all_assets # total_cash defined above
		# 	except Exception, exception:
		# 		print line_number(), exception
		# 		number_of_stocks_at_3_percent = 0
		# 	number_of_stocks_at_3_percent = int(math.floor(number_of_stocks_at_3_percent)) # always round down

		# 	stocks_at_three_percent_cell = [stocks_at_three_percent_row, this_column_number, str(number_of_stocks_at_3_percent)]
		# 	spreadsheet_cell_list.append(stocks_at_three_percent_cell)

		# 	## Approximate to spend on each stock at 3%
		# 	three_percent_of_all_assets_row = 16

		# 	three_persent_in_dollars = "$" + "%.2f" % three_percent_of_all_assets # that %.2f rounds float two decimal places
		# 	three_percent_of_all_assets_cell = [three_percent_of_all_assets_row, this_column_number, three_persent_in_dollars]
		# 	spreadsheet_cell_list.append(three_percent_of_all_assets_cell)

		# # Now, add buy candidate tickers:


		# # Finally, set cell values in list:
		# for cell in spreadsheet_cell_list:
		# 	#print cell
		# 	self.grid.SetCellValue(cell[0],cell[1],cell[2])



		# self.grid.SetGridCursor(cursor_positon[0], cursor_positon[1])
		# self.grid.AutoSizeColumns()
		# print "done building self.grid"
		# self.grid_list.append(self.grid)
	def updateGrid(self, event, grid = None):
		# this function currently creates new grids on top of each other.
		# why?
		# when i tried to update the previous grid using the data (run self.spreadSheetFill on the last line).
		# this caused a Segmentation fault: 11
		# thus, this hack... create a new grid on execution each time.

		if not grid:
			print "no grid"
			grid = self.grid
		else:
			print grid

		row = event.GetRow()
		column = event.GetCol()
		cursor_positon = (int(row), int(column))

		buy_candidates_len = len(self.buy_candidates)
		print buy_candidates_len
		print buy_candidates_len + 1 + self.default_rows_above_buy_candidates + 1
		self.buy_candidates = []
		self.buy_candidate_tuples = []
		for row in (range(buy_candidates_len + 1 + self.default_rows_above_buy_candidates + 1)):
			#print row
			if row > self.default_rows_above_buy_candidates and grid.GetCellBackgroundColour(row, self.default_buy_candidate_column) == "#FAEFCF": # or (250, 239, 207, 255)
				#print row
				ticker = grid.GetCellValue(row, self.default_buy_candidate_column)
				#print ticker
				stock = return_stock_by_symbol(str(ticker).upper())
				if stock:
					self.buy_candidates.append(str(stock.symbol))
					quantity = grid.GetCellValue(row, self.default_buy_candidate_quantity_column)
					if quantity:
						if str(quantity).isdigit():
							quantity = int(quantity)
							ticker_row = row
							self.buy_candidate_tuples.append((ticker_row, quantity))
				else:
					print ticker, "doesn't seem to exist"
		print self.buy_candidates

		# build new grid
		self.newGridFill(cursor_positon = cursor_positon)

	def newGridFill(self, cursor_positon = (0,0) ):
		#print cursor_positon
		
		# CREATE A GRID HERE
		new_grid = TradeGrid(self, -1, size=(1000,650), pos=(0,83))
		# calc rows
		global SALE_PREP_PORTFOLIOS_AND_SALE_CANDIDATES_TUPLE
		global PORTFOLIO_NAMES
		relevant_portfolio_name_list = []
		try:
			self.relevant_portfolios_list = []
			for account in SALE_PREP_PORTFOLIOS_AND_SALE_CANDIDATES_TUPLE[0]:
				id_number = account.id_number
				self.relevant_portfolios_list.append(account)
				relevant_portfolio_name_list.append(PORTFOLIO_NAMES[(id_number - 1)])

			num_rows = len(SALE_PREP_PORTFOLIOS_AND_SALE_CANDIDATES_TUPLE[1])
			global DEFAULT_ROWS_ON_TRADE_PREP_PAGE_FOR_TICKERS
			num_rows += DEFAULT_ROWS_ON_TRADE_PREP_PAGE_FOR_TICKERS
		except Exception, exception:
			print line_number(), exception
			num_rows = 0

		num_rows = max(num_rows, self.default_min_rows, (self.default_rows_above_buy_candidates + len(self.buy_candidates) + 2))
		new_grid.CreateGrid(num_rows, self.default_columns)
		new_grid.Bind(wx.grid.EVT_GRID_CELL_CHANGE, lambda event: self.updateGrid(event, grid = new_grid), new_grid) # self.updateGrid, new_grid)

		#print self.buy_candidates
		for column_num in range(self.default_columns):
			for row_num in range(num_rows):
				if row_num <= self.default_rows_above_buy_candidates or row_num > (self.default_rows_above_buy_candidates + len(self.buy_candidates) + 1) or column_num not in [self.default_buy_candidate_column,14]:
					new_grid.SetReadOnly(row_num, column_num, True)
				elif column_num == self.default_buy_candidate_column:
					new_grid.SetCellBackgroundColour(row_num, column_num, "#FAEFCF")
				elif column_num == 14:
					new_grid.SetCellBackgroundColour(row_num, column_num, "#CFE8FC")


		# Defining cells separately from forming them so they are easy to edit
		# e.g. dummy_cell_var = [Row, Column, "Name/Value"]
		# cell_list = [dummy_cell_var, dummy_cell_2, etc...]
		# for cell in cell_list:
		# 	new_grid.SetCellValue(cell[0],cell[1],cell[2])
		spreadsheet_cell_list = []

		# Start with static values (large if statement for code folding purposes only)
		if "This section sets the static cell values by column" == "This section sets the static cell values by column":
			# Column 0 (using zero-based numbering for simplicity):
			this_column_number = 0

			title_with_relevant_portfolios_string = "Trade Prep (" + ", ".join(relevant_portfolio_name_list) + ")"

			name_of_spreadsheet_cell = [0, this_column_number, title_with_relevant_portfolios_string]
			share_to_sell_cell = [2, this_column_number, "Shares to sell:"]
			ticker_title_cell = [3, this_column_number, "Ticker"]

			spreadsheet_cell_list.append(name_of_spreadsheet_cell)
			spreadsheet_cell_list.append(share_to_sell_cell)
			spreadsheet_cell_list.append(ticker_title_cell)

			# Column 1:
			this_column_number = 1

			num_shares_cell = [3, this_column_number,"# shares"]		
			spreadsheet_cell_list.append(num_shares_cell)

			# Column 2:
			this_column_number = 2

			volume_title_cell = [3, this_column_number, "Volume"]
			spreadsheet_cell_list.append(volume_title_cell)

			# Column 3:
			# empty

			# Column 4:
			this_column_number = 4

			total_asset_cell = [0, this_column_number, "Total asset value ="]
			approximate_surplus_cash_cell = [3, this_column_number, "Approximate surplus cash from sale ="]
			percent_total_cash_cell = [6, this_column_number, "%% Total Cash After Sale"]
			portfolio_cash_available_cell = [9, this_column_number, "Portfolio Cash Available ="]
			num_stocks_to_look_cell = [12, this_column_number, "# of stocks to look at at for 3%% of portfolio each."]
			approximate_to_spend_cell = [15, this_column_number, "Approximate to spend on each (3%) stock."]

			spreadsheet_cell_list.append(total_asset_cell)
			spreadsheet_cell_list.append(approximate_surplus_cash_cell)
			spreadsheet_cell_list.append(percent_total_cash_cell)
			spreadsheet_cell_list.append(portfolio_cash_available_cell)
			spreadsheet_cell_list.append(num_stocks_to_look_cell)
			spreadsheet_cell_list.append(approximate_to_spend_cell)

			# Column 5:
			# empty

			# Column 6:
			this_column_number = 6

			num_symbol_cell = [5, this_column_number, "#"]
			spreadsheet_cell_list.append(num_symbol_cell)

			# Column 7:
			this_column_number = 7

			shares_to_buy_cell = [2, this_column_number, "Shares to buy:"]
			input_ticker_cell = [3, this_column_number, "Input ticker"]

			spreadsheet_cell_list.append(shares_to_buy_cell)
			spreadsheet_cell_list.append(input_ticker_cell)

			# Column 8:
			# empty

			# Column 9:
			# empty

			# Column 10:
			this_column_number = 10

			num_shares_to_buy_cell = [2, this_column_number, "# of shares to buy for"]
			three_percent_cell = [3, this_column_number, "3%"]

			spreadsheet_cell_list.append(num_shares_to_buy_cell)
			spreadsheet_cell_list.append(three_percent_cell)

			# Column 11:
			this_column_number = 11

			for_cell = [2, this_column_number, "for"]
			five_percent_cell = [3, this_column_number, "5%"]

			spreadsheet_cell_list.append(for_cell)
			spreadsheet_cell_list.append(five_percent_cell)

			# Column 12:
			this_column_number = 12

			for_cell_2 = [2, this_column_number, "for"]
			ten_percent_cell = [3, this_column_number, "10%"]

			spreadsheet_cell_list.append(for_cell_2)
			spreadsheet_cell_list.append(ten_percent_cell)

			# Column 13:
			# empty

			# Column 14:
			this_column_number = 14

			input_num_shares_cell = [3, this_column_number, "Input # Shares to Purchase"]
			spreadsheet_cell_list.append(input_num_shares_cell)

			# Column 15:
			this_column_number = 15

			cost_cell = [3, this_column_number, "Cost"]
			spreadsheet_cell_list.append(cost_cell)

			# Column 16: 
			# empty

			# Column 17:
			this_column_number = 17

			total_cost_cell = [1, this_column_number, "Total Cost ="]
			adjusted_cash_cell = [2, this_column_number, "Adjusted Cash Available ="]
			num_stocks_to_purchase_cell = [3, this_column_number, "Number of stocks left to purchase at 3% ="]
			new_cash_percentage_cell = [4, this_column_number, "New cash %% of portfolio ="]
			# this cell may be irrelevant
			# new_cash_total_cell = [5, this_column_number, "New cash %% of total ="]

			spreadsheet_cell_list.append(total_cost_cell)
			spreadsheet_cell_list.append(adjusted_cash_cell)
			spreadsheet_cell_list.append(num_stocks_to_purchase_cell)
			spreadsheet_cell_list.append(new_cash_percentage_cell)
			# spreadsheet_cell_list.append(new_cash_total_cell)

			# Column 18:
			# computed values only

		if "This section sets the variable cell values with relevant data" == "This section sets the variable cell values with relevant data":

			# Column 0-2 data:
			this_column_number = 0
			default_rows = DEFAULT_ROWS_ON_TRADE_PREP_PAGE_FOR_TICKERS # called globally above
			counter = 0
			for stock_tuple in SALE_PREP_PORTFOLIOS_AND_SALE_CANDIDATES_TUPLE[1]:
				ticker = stock_tuple[0]
				number_of_shares_to_sell = stock_tuple[1]
				stock = return_stock_by_symbol(ticker)
				correct_row = counter + default_rows
				
				ticker_cell = [correct_row, this_column_number, ticker]
				number_of_shares_to_sell_cell = [correct_row, (this_column_number + 1), str(number_of_shares_to_sell)]

				spreadsheet_cell_list.append(ticker_cell)
				spreadsheet_cell_list.append(number_of_shares_to_sell_cell)

				try:
					avg_daily_volume = stock.AverageDailyVolume
					volume_cell = [correct_row, (this_column_number + 2), str(avg_daily_volume)]
					spreadsheet_cell_list.append(volume_cell)
				except Exception, exception:
					print line_number(), exception

				counter += 1

			# Column 4 data:
			this_column_number = 4

			## total asset value
			total_asset_value_row = 1

			total_asset_value = 0.00
			for account in self.relevant_portfolios_list:
				total_asset_value += float(account.availble_cash.replace("$",""))
				for stock in account.stock_list:
					stock_data = return_stock_by_symbol(stock.symbol)
					quantity = float(stock.quantity.replace(",",""))
					last_price = float(stock_data.LastTradePriceOnly)
					value_of_held_stock = last_price * quantity
					total_asset_value += value_of_held_stock

			total_asset_value_cell = [total_asset_value_row, this_column_number, ("$" + str(total_asset_value))]
			spreadsheet_cell_list.append(total_asset_value_cell)

			## approximate surplus cash
			approximate_surplus_cash_row = 4

			value_of_all_stock_to_sell = 0.00
			for stock_tuple in SALE_PREP_PORTFOLIOS_AND_SALE_CANDIDATES_TUPLE[1]:
				ticker = stock_tuple[0]
				number_of_shares_to_sell = int(stock_tuple[1])
				stock_data = return_stock_by_symbol(ticker)
				last_price = float(stock_data.LastTradePriceOnly)
				value_of_single_stock_to_sell = last_price * number_of_shares_to_sell
				value_of_all_stock_to_sell += value_of_single_stock_to_sell
			surplus_cash_cell = [approximate_surplus_cash_row, this_column_number, ("$" + str(value_of_all_stock_to_sell))]
			spreadsheet_cell_list.append(surplus_cash_cell)

			## percent of portfolio that is cash after sale
			percent_cash_row = 7
			
			total_cash = 0.00
			for account in self.relevant_portfolios_list:
				total_cash += float(account.availble_cash.replace("$",""))
			total_cash += value_of_all_stock_to_sell
			if total_cash != 0:
				percent_cash = total_cash / total_asset_value
				percent_cash = round(percent_cash * 100)
				percent_cash = str(percent_cash) + "%"
			else:
				percent_cash = "Null"

			percent_cash_cell = [percent_cash_row, this_column_number, percent_cash]
			spreadsheet_cell_list.append(percent_cash_cell)

			## portfolio cash available after sale
			cash_after_sale_row = 10

			total_cash_after_sale = total_cash # from above
			total_cash_after_sale = "$" + str(total_cash_after_sale)

			total_cash_after_sale_cell = [cash_after_sale_row, this_column_number, total_cash_after_sale]
			spreadsheet_cell_list.append(total_cash_after_sale_cell)

			## Number of stocks to purchase at 3% each
			stocks_at_three_percent_row = 13

			three_percent_of_all_assets = 0.03 * total_asset_value # from above
			try:
				number_of_stocks_at_3_percent = total_cash / three_percent_of_all_assets # total_cash defined above
			except Exception, exception:
				print line_number(), exception
				number_of_stocks_at_3_percent = 0
			number_of_stocks_at_3_percent = int(math.floor(number_of_stocks_at_3_percent)) # always round down

			stocks_at_three_percent_cell = [stocks_at_three_percent_row, this_column_number, str(number_of_stocks_at_3_percent)]
			spreadsheet_cell_list.append(stocks_at_three_percent_cell)

			## Approximate to spend on each stock at 3%
			three_percent_of_all_assets_row = 16

			three_persent_in_dollars = "$" + "%.2f" % three_percent_of_all_assets # that %.2f rounds float two decimal places
			three_percent_of_all_assets_cell = [three_percent_of_all_assets_row, this_column_number, three_persent_in_dollars]
			spreadsheet_cell_list.append(three_percent_of_all_assets_cell)

		# Now, add buy candidate tickers:

		count = 0
		# This is the a very similar iteration as above
		for column_num in range(self.default_columns):
			for row_num in range(num_rows):
				if row_num <= self.default_rows_above_buy_candidates or row_num > (self.default_rows_above_buy_candidates + len(self.buy_candidates) + 1) or column_num not in [self.default_buy_candidate_column, self.default_buy_candidate_quantity_column]:
					pass
				elif column_num == self.default_buy_candidate_column:
					if count in range(len(self.buy_candidates)):
						new_grid.SetCellValue(row_num, column_num - 1, str(count + 1))
						new_grid.SetCellValue(row_num, column_num, self.buy_candidates[count])
						
						stock = return_stock_by_symbol(self.buy_candidates[count])
						new_grid.SetCellValue(row_num, column_num + 1, str(stock.Name))

						last_price = float(stock.LastTradePriceOnly)
						new_grid.SetCellValue(row_num, column_num + 2, "$" + str(last_price))

						column_shift = 3
						for percent in [0.03, 0.05, 0.10]:
							# total_asset_value calculated above
							#print total_asset_value
							max_cost = total_asset_value * percent
							#print max_cost
							number_of_shares_to_buy = int(math.floor(max_cost / last_price))
							#print number_of_shares_to_buy
							new_grid.SetCellValue(row_num, column_num + column_shift, str(number_of_shares_to_buy))
							column_shift += 1

						for this_tuple in self.buy_candidate_tuples:
							if this_tuple[0] == row_num:
								new_grid.SetCellValue(row_num, self.default_buy_candidate_quantity_column, str(this_tuple[1]))
					count += 1

		# now calculate final values
		buy_cost_column = 15

		total_buy_cost = 0.00
		for row_num in range(num_rows):
			if row_num > self.default_rows_above_buy_candidates:
				quantity = str(new_grid.GetCellValue(row_num, buy_cost_column - 1))
				if quantity:
					ticker = str(new_grid.GetCellValue(row_num, buy_cost_column - 8))
					print ticker
					stock = return_stock_by_symbol(ticker)
					if stock:
						quantity = int(quantity)
						cost = float(stock.LastTradePriceOnly) * quantity
						total_buy_cost += cost
						cost_cell = [row_num, buy_cost_column, "$" + str(cost)]
						spreadsheet_cell_list.append(cost_cell)

		# column 18 (final column)
		this_column_number = 18

		total_cost_row = 1
		
		total_cost_sum_cell = [total_cost_row, this_column_number, "$" + str(total_buy_cost)]
		spreadsheet_cell_list.append(total_cost_sum_cell)

		adjusted_cash_row = 2
		adjusted_cash_result = total_cash - total_buy_cost
		if adjusted_cash_result >= 0:
			color = "black"
		else:
			color = "red"
		adjusted_cash_result_cell = [adjusted_cash_row, this_column_number, "$" + str(adjusted_cash_result)]
		spreadsheet_cell_list.append(adjusted_cash_result_cell)
		new_grid.SetCellTextColour(adjusted_cash_row, this_column_number, color)

		number_of_stocks_still_yet_to_buy_row = 3
		if total_asset_value > 0:
			number_of_stocks_still_yet_to_buy = int(math.floor(adjusted_cash_result / (total_asset_value * 0.03)))
		else:
			number_of_stocks_still_yet_to_buy = 0
		number_of_stocks_still_yet_to_buy_cell = [number_of_stocks_still_yet_to_buy_row, this_column_number, str(number_of_stocks_still_yet_to_buy)]
		spreadsheet_cell_list.append(number_of_stocks_still_yet_to_buy_cell)
		new_grid.SetCellTextColour(number_of_stocks_still_yet_to_buy_row, this_column_number, color)

		new_percent_cash_row = 4
		if adjusted_cash_result != 0:
			new_percent_cash = round(100 * adjusted_cash_result / total_asset_value)
		else:
			new_percent_cash = 0
		new_percent_cash_cell = [new_percent_cash_row, this_column_number, "%d" % int(new_percent_cash) + "%"]
		spreadsheet_cell_list.append(new_percent_cash_cell)
		new_grid.SetCellTextColour(new_percent_cash_row, this_column_number, color)

		# Finally, set cell values in list:
		for cell in spreadsheet_cell_list:
			#print cell
			new_grid.SetCellValue(cell[0],cell[1],cell[2])



		new_grid.AutoSizeColumns()
		print "done building grid"
		new_grid.SetGridCursor(cursor_positon[0] + 1, cursor_positon[1])

		for grid in self.grid_list:
			grid.Hide()
		self.grid_list.append(new_grid)
		print "number of grids created =", len(self.grid_list)
		new_grid.SetFocus()

class PortfolioPage(Tab):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)
		####
		portfolio_page_panel = wx.Panel(self, -1, pos=(0,5), size=( wx.EXPAND, wx.EXPAND))

		portfolio_account_notebook = wx.Notebook(portfolio_page_panel)
		
		global DATA_ABOUT_PORTFOLIOS
		portfolios_that_already_exist = DATA_ABOUT_PORTFOLIOS[1]
		global NUMBER_OF_PORTFOLIOS		
		portfolio_names = ["Primary", "Secondary", "Tertiary"]

		if not portfolios_that_already_exist:
			new_portfolio_name_list = []
			for i in range(NUMBER_OF_PORTFOLIOS):
				#print line_number(), i
				portfolio_name = None
				if NUMBER_OF_PORTFOLIOS < 10:
					portfolio_name = "Portfolio %d" % (i+1)
				else:
					portfolio_name = "%dth" % (i+1)
				if i in range(len(portfolio_names)):
					portfolio_name = portfolio_names[i]
				portfolio_account = PortfolioAccountTab(portfolio_account_notebook, (i+1))
				portfolio_account_notebook.AddPage(portfolio_account, portfolio_name)

				new_portfolio_name_list.append(portfolio_name)

				DATA_ABOUT_PORTFOLIOS[1] = new_portfolio_name_list
				
				with open('portfolios.pk', 'wb') as output:
					pickle.dump(DATA_ABOUT_PORTFOLIOS, output, pickle.HIGHEST_PROTOCOL)
		else:
			need_to_save = False
			for i in range(NUMBER_OF_PORTFOLIOS):
				#print line_number(), i
				try:
					portfolio_name = portfolios_that_already_exist[i]
				except Exception, exception:
					print line_number(), exception
					if i < 3:
						number_words = ["Primary", "Secondary", "Tertiary"]
						portfolio_name = number_words[i]
					else:
						portfolio_name = "Portfolio %d" % (i+1)
					portfolios_that_already_exist.append(portfolio_name)
					need_to_save = True

				portfolio_account = PortfolioAccountTab(portfolio_account_notebook, (i+1))
				portfolio_account_notebook.AddPage(portfolio_account, portfolio_name)
			if need_to_save == True:

				DATA_ABOUT_PORTFOLIOS[1] = portfolios_that_already_exist
				
				with open('portfolios.pk', 'wb') as output:
					pickle.dump(DATA_ABOUT_PORTFOLIOS, output, pickle.HIGHEST_PROTOCOL)


		if not portfolios_that_already_exist:
			DATA_ABOUT_PORTFOLIOS[1] = new_portfolio_name_list
			with open('portfolios.pk', 'wb') as output:
				pickle.dump(DATA_ABOUT_PORTFOLIOS, output, pickle.HIGHEST_PROTOCOL)
		
		sizer2 = wx.BoxSizer()
		sizer2.Add(portfolio_account_notebook, 1, wx.EXPAND)
		self.SetSizer(sizer2)		
		####
class PortfolioAccountTab(Tab):
	def __init__(self, parent, tab_number):
		tab_panel = wx.Panel.__init__(self, parent, tab_number)
		
		self.portfolio_id = tab_number
		#print line_number(), self.portfolio_id
		try:
			portfolio_file = open('portfolio_%d.pk' % self.portfolio_id, 'rb')
		except Exception, e:
			print line_number(), e
			portfolio_file = open('portfolio_%d.pk' % self.portfolio_id, 'wb')
			new_portfolio_entry = []
			with open('portfolio_%d.pk' % self.portfolio_id, 'wb') as output:
				pickle.dump(new_portfolio_entry, output, pickle.HIGHEST_PROTOCOL)
			portfolio_file = open('portfolio_%d.pk' % self.portfolio_id, 'rb')
		self.portfolio_data = pickle.load(portfolio_file)
		portfolio_file.close()

		global PORTFOLIO_OBJECTS_LIST
		try:
			self.account_obj = PORTFOLIO_OBJECTS_LIST[(int(self.portfolio_id) - 1)]
		except Exception, e:
			print line_number(), e
			try:
				portfolio_account_obj_file = open('portfolio_%d_data.pk' % self.portfolio_id, 'rb')
				self.account_obj = pickle.load(portfolio_account_obj_file)
				PORTFOLIO_OBJECTS_LIST[(int(self.portfolio_id) - 1)] = self.account_obj
				portfolio_account_obj_file.close()
			except Exception, e:
				print line_number(), e
				self.account_obj = None
			# 	portfolio_account_obj_file = open('portfolio_%d_data.pk' % self.portfolio_id, 'wb')
			# 	portfolio_account_obj = []
			# 	with open('portfolio_%d_data.pk' % self.portfolio_id, 'wb') as output:
			# 		pickle.dump(portfolio_account_obj, output, pickle.HIGHEST_PROTOCOL)
			# 	portfolio_account_obj_file = open('portfolio_%d_data.pk' % self.portfolio_id, 'rb')
			# # Why does this error!!!
			

	

		trade_page_text = wx.StaticText(self, -1, 
							 "Your portfolio", 
							 (5,5)
							 )

		add_button = wx.Button(self, label="Add account (Schwab positions .csv)", pos=(100,0), size=(-1,-1))
		add_button.Bind(wx.EVT_BUTTON, self.addAccountCSV, add_button) 

		clear_button = wx.Button(self, label="Clear this portfolio", pos=(830,0), size=(-1,-1))
		clear_button.Bind(wx.EVT_BUTTON, self.confirmDeleteAccount, clear_button) 

		rename_button = wx.Button(self, label="Rename this portfolio", pos=(355,0), size=(-1,-1))
		rename_button.Bind(wx.EVT_BUTTON, self.changeTabName, rename_button) 

		change_number_of_portfolios_button = wx.Button(self, label="Change number of portfolios", pos=(518,0), size=(-1,-1))
		change_number_of_portfolios_button.Bind(wx.EVT_BUTTON, self.changeNumberOfPortfolios, change_number_of_portfolios_button) 

		#print_portfolio_data_button = wx.Button(self, label="p", pos=(730,0), size=(-1,-1))
		#print_portfolio_data_button.Bind(wx.EVT_BUTTON, self.printData, print_portfolio_data_button) 

		self.current_account_spreadsheet = AccountDataGrid(self, -1, size=(980,637), pos=(0,50))
		self.spreadSheetFill(self.current_account_spreadsheet, self.portfolio_data)
	def printData(self, event):
		if self.account_obj:
			print line_number(),"cash:", self.account_obj.availble_cash
			for account_attribute in dir(self.account_obj):
				if not account_attribute.startswith("_"):
					print line_number(),account_attribute, ":"
					try:
						for stock_attribute in dir(getattr(self.account_obj, account_attribute)):
							if not stock_attribute.startswith("_"):
								print line_number(),stock_attribute, getattr(getattr(self.account_obj, account_attribute), stock_attribute)
					except Exception, exception:
						print line_number(),exception
	def changeNumberOfPortfolios(self, event):
		global NUMBER_OF_PORTFOLIOS
		num_of_portfolios_popup = wx.NumberEntryDialog(None,
									  "What would you like to call this portfolio?", 
									  "Rename tab",
									  "Caption", 
									  NUMBER_OF_PORTFOLIOS,
									  0,
									  10
									  )
		if num_of_portfolios_popup.ShowModal() != wx.ID_OK:
			return

		new_number_of_portfolios = num_of_portfolios_popup.GetValue()
		num_of_portfolios_popup.Destroy()

		NUMBER_OF_PORTFOLIOS = new_number_of_portfolios
		DATA_ABOUT_PORTFOLIOS[0] = new_number_of_portfolios
		with open('portfolios.pk', 'wb') as output:
			pickle.dump(DATA_ABOUT_PORTFOLIOS, output, pickle.HIGHEST_PROTOCOL)
		confirm = wx.MessageDialog(self,
								 "The number of portfolios has changed. The change will be applied the next time you launch this program.",
								 'Restart Required',
								 style = wx.ICON_EXCLAMATION
								 )
		confirm.ShowModal()
		confirm.Destroy()
	def spreadSheetFill(self, spreadsheet, account_data):
		self.current_account_spreadsheet.Destroy()

		num_rows = len(account_data)
		columns = 0
		for row in account_data:
			num_cells = 0
			for cell in row:
				num_cells += 1
			if num_cells > columns:
				columns = num_cells
		num_columns = columns
		spreadsheet = AccountDataGrid(self, -1, size=(980,637), pos=(0,50))
		spreadsheet.CreateGrid(num_rows, num_columns)
		spreadsheet.EnableEditing(False)

		row_count = 0
		col_count = 0
		for row in account_data:
			for cell in row:
				#if not attribute.startswith('_'):
				if row_count == 0:
					pass
				elif row_count == 1:
					spreadsheet.SetColLabelValue(col_count, str(cell))
				else:
					try:
						spreadsheet.SetCellValue(row_count - 2, col_count, str(cell))
					except:
						pass
				col_count += 1
			row_count += 1
			col_count = 0
		spreadsheet.AutoSizeColumns()
		self.current_account_spreadsheet = spreadsheet
	def addAccountCSV(self, event):
		'''append a csv to current ticker list'''
		self.dirname = ''
		dialog = wx.FileDialog(self, "Choose a file", self.dirname, "", "*.csv", wx.OPEN)
		if dialog.ShowModal() == wx.ID_OK:
			self.filename = dialog.GetFilename()
			self.dirname = dialog.GetDirectory()
			
			new_account_file = open(os.path.join(self.dirname, self.filename), 'rb')
			new_account_file_data = self.importSchwabCSV(new_account_file)
			self.portfolio_data = new_account_file_data
			new_account_file.close()

			with open('portfolio_%d.pk' % self.portfolio_id, 'wb') as output:
				pickle.dump(self.portfolio_data, output, pickle.HIGHEST_PROTOCOL)

			new_account_stock_list = []
			cash = "This should be changed"
			count = 0
			for row in self.portfolio_data:
				print line_number(),count
				if count <= 1:
					count += 1
					continue
				try:
					if row[0] and row[11]:
						if str(row[11]) == "Cash & Money Market":
							cash = row[5]
							print line_number(),'cash'
						elif str(row[11]) == "Equity":
							# format: ticker(0), name(1), quantity(2), price(3), change(4), market value(5), day change$(6), day change%(7), reinvest dividends?(8), capital gain(9), percent of account(10), security type(11)
							# HeldStock.__init__(self, symbol, quantity, security_type)
							stock_to_add = HeldStock(row[0], row[2], row[11])
							new_account_stock_list.append(stock_to_add)
							print line_number(),"stock"
				except Exception, exception:
					print line_number(),exception
					print line_number(),row
				count += 1
			if cash == "This should be changed":
				logging.error('Formatting error in CSV import')
			# Account.__init__(self, cash, stock_list)
			self.account_obj = Account(self.portfolio_id, cash, new_account_stock_list)
			with open('portfolio_%d_data.pk' % self.portfolio_id, 'wb') as output:
				pickle.dump(self.account_obj, output, pickle.HIGHEST_PROTOCOL)
			self.spreadSheetFill(self.current_account_spreadsheet, self.portfolio_data)
			PORTFOLIO_OBJECTS_LIST[(int(self.portfolio_id) - 1)] = self.account_obj
		dialog.Destroy()
	def importSchwabCSV(self, csv_file):
		reader = csv.reader(csv_file)
		row_list = []
		for row in reader:
			row_list.append(row)
		washed_row_list = []
		for row in row_list:
			if row:
				washed_row = []
				for cell in row:
					washed_cell = strip_string_whitespace(cell)
					washed_row.append(washed_cell)
				washed_row_list.append(washed_row)
		return washed_row_list
	def changeTabName(self, event):
		old_name = self.GetLabel()
		rename_popup = wx.TextEntryDialog(None,
									  "What would you like to call this portfolio?", 
									  "Rename tab", 
									  str(self.GetLabel())
									  )
		rename_popup.ShowModal()
		new_name = str(rename_popup.GetValue())
		rename_popup.Destroy()

		global DATA_ABOUT_PORTFOLIOS
		portfolio_name_list = DATA_ABOUT_PORTFOLIOS[1]
		new_portfolio_names = []
		if new_name != old_name:
			if new_name not in portfolio_name_list:
				for i in portfolio_name_list:
					if i == old_name:
						new_portfolio_names.append(new_name)
					else:
						new_portfolio_names.append(i)
				DATA_ABOUT_PORTFOLIOS[1] = new_portfolio_names
				with open('portfolios.pk', 'wb') as output:
					pickle.dump(DATA_ABOUT_PORTFOLIOS, output, pickle.HIGHEST_PROTOCOL)
				print line_number(),DATA_ABOUT_PORTFOLIOS
				confirm = wx.MessageDialog(self,
										 "This portfolio's name has been changed. The change will be applied the next time you launch this program.",
										 'Restart Required',
										 style = wx.ICON_EXCLAMATION
										 )
				confirm.ShowModal()
				confirm.Destroy()

			else:
				error = wx.MessageDialog(self,
										 'Each portfolio must have a unique name.',
										 'Name Error',
										 style = wx.ICON_ERROR
										 )
				error.ShowModal()
				error.Destroy()
	def confirmDeleteAccount(self, event):
		confirm = wx.MessageDialog(None, 
								   "You are about to delete your current account data. Are you sure you want to delete this data?", 
								   'Delete Portfolio Data?', 
								   wx.YES_NO
								   )
		confirm.SetYesNoLabels(("&Delete"), ("&Cancel"))
		yesNoAnswer = confirm.ShowModal()
		confirm.Destroy()

		if yesNoAnswer == wx.ID_YES:
			self.deleteAccountList()

	def deleteAccountList(self):
		'''delete account'''
		self.portfolio_data = []
		# opening the file with w+ mode truncates the file
		with open('portfolio_%d.pk' % self.portfolio_id, 'wb') as output:
			pickle.dump(self.portfolio_data, output, pickle.HIGHEST_PROTOCOL)
		self.current_account_spreadsheet.Destroy()
		self.current_account_spreadsheet = AccountDataGrid(self, -1, size=(980,637), pos=(0,50))
		self.spreadSheetFill(self.current_account_spreadsheet, self.portfolio_data)
		self.account_obj = None
		PORTFOLIO_OBJECTS_LIST[(int(self.portfolio_id) - 1)] = self.account_obj

####################### Screening functions #######################
def screen_pe_less_than_10():
	global GLOBAL_STOCK_LIST
	screen = []
	for stock in GLOBAL_STOCK_LIST:
		try:
			if stock.PERatio:
				if float(stock.PERatio) < 10:
					screen.append(stock)
		except Exception, e:
			print line_number(),e
	return screen
####################### Pickle functions #######################
def saveStocks(obj, stock_list):
	with open(filename, 'wb') as output:
		pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)

#saveobject(company1, r'c:\mypythonobject')
####################### Utility functions #######################
def gen_ticker_list(csv_file):
	reader = csv.reader(csv_file)
	reader_list = []
	for row in reader:
		reader_list.append(row)
	ticker_list = []
	for row in reader_list:
		if row:
			if row[0] != "Symbol":
				ticker_list.append(row[0])
	ticker_list = strip_list_whitespace(ticker_list)
	ticker_list.sort()
	return ticker_list
def return_list_of_lists(csv_file):
	full_data = []
	reader = csv.reader(csv_file)
	for row in reader:
		full_data.append(list(row))
	#print line_number(),full_data
	return full_data
def openCSV_return_list_of_lists():
	csv_file = filedialog.askopenfile()
	print line_number(),'opening', csv_file
	try:
		ticker_list = return_list_of_lists(csv_file)
		return ticker_list
	except:
		error_label = Label(main_tab, text='You must import a csv file.')
		error_label.pack()
		return
def remove_list_duplicates(some_list):
	if type(some_list) != "list":
		some_list = list(some_list)
	the_set = set(some_list)
	new_list = list(the_set)
	return new_list
def strip_list_whitespace(some_list):
	tag_list = some_list
	#logging.warning(tag_list)
	new_list = []
	for tag in tag_list:
		tag = " ".join(tag.split())
		new_list.append(tag)
	tag_list = new_list
	new_list = []
	for tag in tag_list:
		if tag:
			new_list.append(tag)
	return new_list
def strip_string_whitespace(some_string):
	stripped_string = " ".join(some_string.split())
	return stripped_string
def time_since_creation(item_epoch_var):
	raw_secs = round(time.time())-round(item_epoch_var)
	#logging.warning(raw_secs)
	raw_secs = int(raw_secs)
	time_str = None
	if raw_secs < 60:
		seconds = raw_secs
		if seconds > 1:
			time_str = "%d seconds" % seconds
		else:
			time_str = "%d second" % seconds
	elif (raw_secs >= 60) and (raw_secs < (60 * 60)):
		minutes = (raw_secs/60)
		if minutes > 1:
			time_str = "%d minutes" % minutes
		else:
			time_str = "%d minute" % minutes
	elif (raw_secs >= (60*60) and (raw_secs < (60 * 60 * 24))):
		minutes = (raw_secs/60)
		hours = (minutes/60)
		if hours > 1:
			time_str = "%d hours" % hours
		else:
			time_str = "%d hour" % hours
	elif (raw_secs >= (60*60*24) and (raw_secs < (60*60*24*30))):
		minutes = (raw_secs/60)
		hours = (minutes/60)
		days = (hours/24)
		if days > 1:
			time_str = "%d days" % days
		else:
			time_str = "%d day" % days
	elif (raw_secs >=(60*60*24*30)) and (raw_secs < (60*60*24*365)):		
		minutes = (raw_secs/60)
		hours = (minutes/60)
		days = (hours/24)
		months = (days/30)
		if months > 1:
			time_str = "%d months" % months
		else:
			time_str = "%d month" % months
	elif raw_secs >= (60*60*24*365):
		minutes = (raw_secs/60)
		hours = (minutes/60)
		days = (hours/24)
		years = (days/365)
		if years > 1:
			time_str = "%d years" % years
		else:
			time_str = "%d year" % years
	else:
		logging.error("something wrong with time_since_creation function")
		time_str = None
	return time_str		
def check_url(url_str):
	link_var = url_str
	deadLinkFound = check_url_instance(link_var)
	if deadLinkFound:
		link_var = "http://" + link_var
		deadLinkFound = check_url_instance(link_var)
		if deadLinkFound:
			link_var = "http://www." + link_var
			deadLinkFound = check_url_instance(link_var)
			if deadLinkFound:
				link_var = None
	return link_var
def check_url_instance(url_str):
	link_var = url_str
	logging.warning(link_var)
	deadLinkFound = True
	try:
		f = urlfetch.fetch(url=link_var, deadline=30)
		if f.status_code == 200:
			#logging.warning(f.content)
			pass
		deadLinkFound = False
	except Exception as e:
		logging.warning('that failed')
		logging.warning(e)
	logging.warning(deadLinkFound)
	return deadLinkFound
def remove_unsafe_chars_from_tags(tag_list):
	escaped_list = []
	for tag in tag_list:
		escaped_string = []
		for char in tag:
			if char in URL_SAFE_CHARS:
				escaped_string.append(char)
			else:
				if char == " ":
					escaped_string.append("_")
		tag = "".join(escaped_string)
		escaped_list.append(tag)
	new_tag_list = escaped_list
	return new_tag_list 
def time_from_epoch(item_epoch_var):
	raw_secs = round(item_epoch_var)
	#logging.warning(raw_secs)
	raw_secs = int(raw_secs)
	time_str = None
	if raw_secs < 60:
		seconds = raw_secs
		if seconds > 1:
			time_str = "%d seconds" % seconds
		else:
			time_str = "%d second" % seconds
	elif (raw_secs >= 60) and (raw_secs < (60 * 60)):
		minutes = (raw_secs/60)
		if minutes > 1:
			time_str = "%d minutes" % minutes
		else:
			time_str = "%d minute" % minutes
	elif (raw_secs >= (60*60) and (raw_secs < (60 * 60 * 24))):
		minutes = (raw_secs/60)
		hours = (minutes/60)
		if hours > 1:
			time_str = "%d hours" % hours
		else:
			time_str = "%d hour" % hours
	elif (raw_secs >= (60*60*24) and (raw_secs < (60*60*24*30))):
		minutes = (raw_secs/60)
		hours = (minutes/60)
		days = (hours/24)
		if days > 1:
			time_str = "%d days" % days
		else:
			time_str = "%d day" % days
	elif (raw_secs >=(60*60*24*30)) and (raw_secs < (60*60*24*365)):		
		minutes = (raw_secs/60)
		hours = (minutes/60)
		days = (hours/24)
		months = (days/30)
		if months > 1:
			time_str = "%d months" % months
		else:
			time_str = "%d month" % months
	elif raw_secs >= (60*60*24*365):
		minutes = (raw_secs/60)
		hours = (minutes/60)
		days = (hours/24)
		years = (days/365)
		if years > 1:
			time_str = "%d years" % years
		else:
			time_str = "%d year" % years
	else:
		logging.error("something wrong with time_from_epoch function")
		time_str = None
	return time_str	
def return_stock_by_symbol(ticker_symbol):
	global GLOBAL_STOCK_LIST
	for stock in GLOBAL_STOCK_LIST:
		if stock.symbol == ticker_symbol:
			return stock
	#if the function does not return a stock
	return None
def is_number(some_string):
	try:
		float(some_string)
		return True
	except Exception, exception:
		# print exception
		return False
def relevant_float(some_float):
	return (some_float - int(some_float)) != 0

app = None
def main():
	global app
	app = wx.App()
	MainFrame(size=(1020,800), #style = wx.MINIMIZE_BOX | wx.CLOSE_BOX
			  ).Show()
	app.MainLoop()
main()

