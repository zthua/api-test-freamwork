"""
创建测试用Excel文件
"""

try:
    import openpyxl
    from openpyxl import Workbook
    
    # 创建工作簿
    wb = Workbook()
    ws = wb.active
    ws.title = "PaymentData"
    
    # 写入表头
    headers = ["case_id", "payment_method", "amount", "currency", "expected_status"]
    ws.append(headers)
    
    # 写入数据
    data = [
        ["TC001", "WECHAT_NATIVE", 100.00, "CNY", "SUCCESS"],
        ["TC002", "ALIPAY_APP", 200.50, "CNY", "SUCCESS"],
        ["TC003", "CLOUDPAY_APP", 50.00, "CNY", "SUCCESS"],
        ["TC004", "WECHAT_JSAPI", 0.01, "CNY", "SUCCESS"],
        ["TC005", "ALIPAY_H5", 999.99, "CNY", "SUCCESS"],
    ]
    
    for row in data:
        ws.append(row)
    
    # 保存文件
    wb.save("api-test-framework/testdata/payment_data.xlsx")
    print("Excel file created successfully: api-test-framework/testdata/payment_data.xlsx")
    
except ImportError:
    print("openpyxl not installed. Skipping Excel file creation.")
    print("Install with: pip install openpyxl")
