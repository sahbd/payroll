

class SalarySheetCalculations:
	@staticmethod
	def calculate_percentage_from_basic(basic_pay, personal_pay, percentage):
		return (basic_pay + personal_pay) * percentage / 100

	@staticmethod
	def calculate_default_values(basic_pay, personal_pay, default_value, is_percentage):
		if is_percentage:
			return (basic_pay + personal_pay) * default_value / 100
		else:
			return default_value

	@staticmethod
	def calculate_gpf_interest(date, deduction):
		def get_working_month(date):
			month = date.month
			if month > 6:
				return 12 - (6 + month) % 13
			else:
				return 13 - (6 + month) % 13

		return deduction * (13 / 12 * get_working_month(date))/100;

	@staticmethod
	def calculate_gpf_interest_for_year(deduction):
		return deduction * 13 /100;



