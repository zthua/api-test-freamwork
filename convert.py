#!/usr/bin/env python3
"""
测试用例转换命令行工具

提供命令行接口,将Markdown格式的测试用例文档转换为可执行的pytest代码
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.conversion_workflow import ConversionWorkflow
from utils.logger import Logger


def parse_arguments():
    """解析命令行参数
    
    Returns:
        解析后的参数对象
    """
    parser = argparse.ArgumentParser(
        description='测试用例转换工具 - 将Markdown测试用例转换为可执行的pytest代码',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本用法 - 转换测试用例文档
  python3 convert.py -i ../统一创单接口createpay测试用例.md
  
  # 指定输出目录
  python3 convert.py -i test_cases.md -o testcases/custom
  
  # 按支付方式分组
  python3 convert.py -i test_cases.md -g payment_method
  
  # 只转换特定支付模式
  python3 convert.py -i test_cases.md -f direct,account
  
  # 不保存解析数据
  python3 convert.py -i test_cases.md --no-save-parsed
  
  # 详细输出
  python3 convert.py -i test_cases.md -v
        """
    )
    
    # 必需参数
    parser.add_argument(
        '-i', '--input',
        required=True,
        help='输入的Markdown测试用例文件路径'
    )
    
    # 可选参数
    parser.add_argument(
        '-o', '--output',
        default='testcases/generated',
        help='输出目录路径 (默认: testcases/generated)'
    )
    
    parser.add_argument(
        '-t', '--template-dir',
        default='templates',
        help='模板目录路径 (默认: templates)'
    )
    
    parser.add_argument(
        '-g', '--group-by',
        choices=['payment_mode', 'payment_method', 'priority'],
        default='payment_mode',
        help='测试用例分组方式 (默认: payment_mode)'
    )
    
    parser.add_argument(
        '-f', '--filter',
        help='过滤特定的支付模式或支付方式,多个值用逗号分隔 (例如: direct,account)'
    )
    
    parser.add_argument(
        '--no-save-parsed',
        action='store_true',
        help='不保存解析后的JSON数据'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='详细输出模式'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='日志级别 (默认: INFO)'
    )
    
    return parser.parse_args()


def apply_filter(test_cases, filter_values, group_by):
    """应用过滤器
    
    Args:
        test_cases: 测试用例列表
        filter_values: 过滤值列表
        group_by: 分组方式
        
    Returns:
        过滤后的测试用例列表
    """
    if not filter_values:
        return test_cases
    
    filter_set = set(filter_values.split(','))
    filtered = []
    
    for tc in test_cases:
        if group_by == 'payment_mode':
            if tc.payment_mode in filter_set:
                filtered.append(tc)
        elif group_by == 'payment_method':
            if tc.payment_method in filter_set:
                filtered.append(tc)
        elif group_by == 'priority':
            if tc.priority in filter_set:
                filtered.append(tc)
    
    return filtered


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()
    
    # 初始化日志记录器
    log_level = 'DEBUG' if args.verbose else args.log_level
    logger = Logger(name="ConvertCLI", level=log_level, log_dir="logs")
    
    logger.info("=" * 80)
    logger.info("测试用例转换工具启动")
    logger.info("=" * 80)
    
    # 验证输入文件
    input_file = Path(args.input)
    if not input_file.exists():
        logger.error(f"输入文件不存在: {input_file}")
        return 1
    
    logger.info(f"输入文件: {input_file.absolute()}")
    logger.info(f"输出目录: {args.output}")
    logger.info(f"分组方式: {args.group_by}")
    
    if args.filter:
        logger.info(f"过滤条件: {args.filter}")
    
    try:
        # 初始化转换流程编排器
        workflow = ConversionWorkflow(
            template_dir=args.template_dir,
            output_dir=args.output,
            logger=logger
        )
        
        # 步骤1: 解析测试用例
        logger.info("\n步骤1: 解析测试用例...")
        test_cases = workflow.parse_test_cases(str(input_file))
        logger.info(f"✓ 成功解析 {len(test_cases)} 个测试用例")
        
        # 步骤2: 应用过滤器(如果有)
        if args.filter:
            logger.info("\n步骤2: 应用过滤器...")
            original_count = len(test_cases)
            test_cases = apply_filter(test_cases, args.filter, args.group_by)
            logger.info(f"✓ 过滤后剩余 {len(test_cases)} 个测试用例 (原始: {original_count})")
        
        # 步骤3: 构建接口对象
        logger.info("\n步骤3: 构建接口对象...")
        api_objects = workflow.build_api_objects(test_cases)
        logger.info(f"✓ 识别到 {len(api_objects['payment_methods'])} 种支付方式")
        logger.info(f"✓ 识别到 {len(api_objects['payment_modes'])} 种支付模式")
        
        # 步骤4: 生成测试代码
        logger.info("\n步骤4: 生成测试代码...")
        generated_files = workflow.generate_test_code(test_cases, group_by=args.group_by)
        logger.info(f"✓ 生成 {len(generated_files)} 个测试文件")
        
        # 步骤5: 获取文件路径
        logger.info("\n步骤5: 保存文件...")
        saved_files = workflow.save_generated_files(generated_files)
        
        # 步骤6: 保存解析数据(可选)
        parsed_file = None
        if not args.no_save_parsed:
            logger.info("\n步骤6: 保存解析数据...")
            parsed_file = workflow.save_parsed_data(test_cases, output_format="json")
            logger.info(f"✓ 解析数据已保存: {parsed_file}")
        
        # 输出总结
        logger.info("\n" + "=" * 80)
        logger.info("转换成功!")
        logger.info("=" * 80)
        logger.info(f"解析用例数: {len(test_cases)}")
        logger.info(f"生成文件数: {len(saved_files)}")
        logger.info("\n生成的文件:")
        for file_path in saved_files:
            logger.info(f"  ✓ {file_path}")
        
        if parsed_file:
            logger.info(f"\n解析数据: {parsed_file}")
        
        logger.info("\n接口对象信息:")
        logger.info(f"  支付方式: {', '.join(sorted(api_objects['payment_methods']))}")
        logger.info(f"  支付模式: {', '.join(sorted(api_objects['payment_modes']))}")
        
        return 0
        
    except Exception as e:
        logger.error("\n" + "=" * 80)
        logger.error("转换失败!")
        logger.error("=" * 80)
        logger.error(f"错误信息: {str(e)}")
        
        if args.verbose:
            import traceback
            logger.error("\n详细错误信息:")
            logger.error(traceback.format_exc())
        
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
