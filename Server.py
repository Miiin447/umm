from logic.dataProcessing import DataProcessing





if __name__ == "__main__":
    backend = DataProcessing()
    result = backend.run_table_update("회원-sales.xlsx", "Patients.csv", "PaymentItems.csv")
    print(result) 




    