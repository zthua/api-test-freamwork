"""
测试用例转换执行脚本

执行完整的测试用例转换流程,将Markdown测试用例转换为可执行的pytest代码
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.conversion_workflow import ConversionWorkflow
from utils.logger import Logger


def main():
    """主函数"""
    # 初始化日志记录器
    logger = Logger(name="ConversionScript", log_dir="logs")
    
    logger.info("=" * 80)
    logger.info("测试用例转换脚本启动")
    logger.info("=" * 80)
    
    # Markdown测试用例文件路径(在项目根目录)
    # 脚本在api-test-framework目录下,所以需要..回到根目录
    project_root = Path(__file__).parent.parent
    markdown_file = project_root / "统一创单接口createpay测试用例.md"
    
    # 检查文件是否存在
    if not markdown_file.exists():
        logger.error(f"测试用例文件不存在: {markdown_file}")
        logger.error("请确保文件路径正确")
        return 1
    
    logger.info(f"测试用例文件: {markdown_file.absolute()}")
    
    # 初始化转换流程编排器
    workflow = ConversionWorkflow(
        template_dir="templates",
        output_dir="testcases/generated",
        logger=logger
    )
    
    # 执行完整转换流程
    result = workflow.run_full_conversion(
        markdown_file=str(markdown_file),
        group_by="payment_mode",  # 按支付模式分组
        save_parsed=True  # 保存解析后的数据
    )
    
    # 输出结果
    if result['success']:
        logger.info("\n" + "=" * 80)
        logger.info("转换成功!")
        logger.info("=" * 80)
        logger.info(f"解析用例数: {result['test_cases_count']}")
        logger.info(f"生成文件数: {len(result['generated_files'])}")
        logger.info(f"耗时: {result['elapsed_time']:.2f}秒")
        logger.info("\n生成的文件:")
        for file_path in result['generated_files']:
            logger.info(f"  - {file_path}")
        
        if result['parsed_data_file']:
            logger.info(f"\n解析数据文件: {result['parsed_data_file']}")
        
        logger.info("\n接口对象信息:")
        logger.info(f"  - 支付方式: {', '.join(result['api_objects']['payment_methods'])}")
        logger.info(f"  - 支付模式: {', '.join(result['api_objects']['payment_modes'])}")
        logger.info(f"  - 请求字段数: {len(result['api_objects']['request_fields'])}")
        logger.info(f"  - 响应字段数: {len(result['api_objects']['response_fields'])}")
        
        return 0
    else:
        logger.error("\n" + "=" * 80)
        logger.error("转换失败!")
        logger.error("=" * 80)
        logger.error(f"错误信息: {result['error']}")
        logger.error(f"耗时: {result['elapsed_time']:.2f}秒")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
