#!/usr/bin/env python3
"""
数据库诊断脚本

提供SQL查询用于诊断文献调研功能在数据库中的状态。
这些查询需要用户手动连接到Render PostgreSQL数据库执行。

使用说明：
1. 获取Render数据库连接信息：Render Dashboard → PostgreSQL数据库 → Connection
2. 使用pgAdmin、psql、DBeaver等工具连接到数据库
3. 执行本脚本生成的SQL查询

环境变量：
- 无需环境变量，本脚本只生成SQL查询语句
"""

import os
import sys

def safe_print(message):
    """安全打印，处理Windows编码问题"""
    try:
        print(message)
    except UnicodeEncodeError:
        # 在Windows命令行（GBK编码）下处理Unicode字符
        print(message.encode("utf-8", errors="replace").decode("gbk", errors="replace"))

def generate_sql_queries():
    """生成数据库诊断SQL查询"""
    safe_print("=" * 80)
    safe_print("文献调研功能数据库诊断查询")
    safe_print("=" * 80)
    safe_print("\n说明：")
    safe_print("1. 登录Render Dashboard：https://dashboard.render.com/")
    safe_print("2. 导航到PostgreSQL数据库：otium-database")
    safe_print("3. 点击'Connection'标签获取连接信息")
    safe_print("4. 使用连接信息连接到数据库")
    safe_print("5. 执行以下SQL查询")
    safe_print("-" * 80)

    # SQL查询1：查看文献调研任务状态
    sql1 = """
-- ============================================
-- 查询1：查看最近的文献调研任务状态
-- ============================================
SELECT
    id,
    task_type,
    status,
    attempts,
    progress_percentage,
    current_step,
    total_steps,
    step_description,
    created_at,
    updated_at,
    result_data IS NOT NULL as has_result_data,
    error_message
FROM background_tasks
WHERE task_type LIKE '%literature%' OR task_type LIKE '%deep%'
ORDER BY created_at DESC
LIMIT 10;
"""

    # SQL查询2：查看任务结果数据
    sql2 = """
-- ============================================
-- 查询2：查看已完成任务的結果数据
-- ============================================
SELECT
    id,
    task_type,
    status,
    result_data->>'text' as result_text_preview,
    LENGTH(result_data->>'text') as result_length,
    created_at,
    updated_at
FROM background_tasks
WHERE task_type LIKE '%literature%'
    AND status = 'COMPLETED'
    AND result_data IS NOT NULL
ORDER BY created_at DESC
LIMIT 5;
"""

    # SQL查询3：查看失败任务
    sql3 = """
-- ============================================
-- 查询3：查看失败的任务
-- ============================================
SELECT
    id,
    task_type,
    status,
    attempts,
    error_message,
    created_at,
    updated_at
FROM background_tasks
WHERE task_type LIKE '%literature%'
    AND status = 'FAILED'
ORDER BY created_at DESC
LIMIT 10;
"""

    # SQL查询4：检查后台工作器相关的任务
    sql4 = """
-- ============================================
-- 查询4：检查不同类型任务的状态分布
-- ============================================
SELECT
    task_type,
    status,
    COUNT(*) as count,
    AVG(EXTRACT(EPOCH FROM (updated_at - created_at))) as avg_duration_seconds,
    MAX(created_at) as latest_task
FROM background_tasks
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY task_type, status
ORDER BY task_type, status;
"""

    # SQL查询5：查看长时间运行的任务
    sql5 = """
-- ============================================
-- 查询5：查看长时间运行或卡住的任务
-- ============================================
SELECT
    id,
    task_type,
    status,
    attempts,
    created_at,
    updated_at,
    EXTRACT(EPOCH FROM (NOW() - created_at)) as age_seconds,
    EXTRACT(EPOCH FROM (NOW() - updated_at)) as inactive_seconds
FROM background_tasks
WHERE status IN ('PENDING', 'PROCESSING')
    AND created_at < NOW() - INTERVAL '5 minutes'
ORDER BY created_at DESC
LIMIT 10;
"""

    safe_print("\n查询1：最近的文献调研任务状态")
    safe_print("-" * 40)
    safe_print(sql1)

    safe_print("\n查询2：已完成任务的结果数据")
    safe_print("-" * 40)
    safe_print(sql2)

    safe_print("\n查询3：失败的任务")
    safe_print("-" * 40)
    safe_print(sql3)

    safe_print("\n查询4：任务状态分布（过去7天）")
    safe_print("-" * 40)
    safe_print(sql4)

    safe_print("\n查询5：长时间运行的任务")
    safe_print("-" * 40)
    safe_print(sql5)

    # 生成诊断建议
    safe_print("\n" + "=" * 80)
    safe_print("诊断建议")
    safe_print("=" * 80)

    safe_print("\n根据查询结果，检查以下问题：")
    safe_print("\n1. 任务状态分布：")
    safe_print("   - 是否有大量PENDING状态的任务？ → 可能后台工作器未运行")
    safe_print("   - 是否有大量FAILED状态的任务？ → 检查错误信息")
    safe_print("   - 任务平均处理时间是否正常？")

    safe_print("\n2. 任务结果数据：")
    safe_print("   - 已完成任务是否有result_data？")
    safe_print("   - result_data.text字段是否有内容？")
    safe_print("   - 结果长度是否合理？")

    safe_print("\n3. 失败任务分析：")
    safe_print("   - error_message字段显示什么错误？")
    safe_print("   - 失败任务的重试次数(attempts)是多少？")

    safe_print("\n4. 长时间运行的任务：")
    safe_print("   - 是否有任务卡在PENDING或PROCESSING状态超过5分钟？")
    safe_print("   - 这些任务可能被卡住，需要手动干预")

    safe_print("\n" + "=" * 80)
    safe_print("常见问题解决方案")
    safe_print("=" * 80)

    safe_print("\n1. 后台工作器未运行：")
    safe_print("   - 检查Render Dashboard中otium-background-worker服务状态")
    safe_print("   - 确认ENABLE_BACKGROUND_WORKER=true")
    safe_print("   - 查看工作器日志")

    safe_print("\n2. MANUS API密钥问题：")
    safe_print("   - 检查MANUS_API_KEY环境变量")
    safe_print("   - 验证API密钥是否有效且有额度")

    safe_print("\n3. 数据库连接问题：")
    safe_print("   - 检查DATABASE_URL连接字符串")
    safe_print("   - 验证PostgreSQL数据库服务状态")

    safe_print("\n4. 任务处理失败：")
    safe_print("   - 查看error_message字段的具体错误")
    safe_print("   - 检查任务处理逻辑是否正常")

def save_sql_to_file():
    """将SQL查询保存到文件"""
    sql_content = """-- 文献调研功能数据库诊断查询
-- 生成时间：2026-02-28
-- 说明：连接到Render PostgreSQL数据库后执行以下查询

-- ============================================
-- 查询1：查看最近的文献调研任务状态
-- ============================================
SELECT
    id,
    task_type,
    status,
    attempts,
    progress_percentage,
    current_step,
    total_steps,
    step_description,
    created_at,
    updated_at,
    result_data IS NOT NULL as has_result_data,
    error_message
FROM background_tasks
WHERE task_type LIKE '%literature%' OR task_type LIKE '%deep%'
ORDER BY created_at DESC
LIMIT 10;

-- ============================================
-- 查询2：查看已完成任务的結果数据
-- ============================================
SELECT
    id,
    task_type,
    status,
    result_data->>'text' as result_text_preview,
    LENGTH(result_data->>'text') as result_length,
    created_at,
    updated_at
FROM background_tasks
WHERE task_type LIKE '%literature%'
    AND status = 'COMPLETED'
    AND result_data IS NOT NULL
ORDER BY created_at DESC
LIMIT 5;

-- ============================================
-- 查询3：查看失败的任务
-- ============================================
SELECT
    id,
    task_type,
    status,
    attempts,
    error_message,
    created_at,
    updated_at
FROM background_tasks
WHERE task_type LIKE '%literature%'
    AND status = 'FAILED'
ORDER BY created_at DESC
LIMIT 10;

-- ============================================
-- 查询4：检查不同类型任务的状态分布
-- ============================================
SELECT
    task_type,
    status,
    COUNT(*) as count,
    AVG(EXTRACT(EPOCH FROM (updated_at - created_at))) as avg_duration_seconds,
    MAX(created_at) as latest_task
FROM background_tasks
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY task_type, status
ORDER BY task_type, status;

-- ============================================
-- 查询5：查看长时间运行或卡住的任务
-- ============================================
SELECT
    id,
    task_type,
    status,
    attempts,
    created_at,
    updated_at,
    EXTRACT(EPOCH FROM (NOW() - created_at)) as age_seconds,
    EXTRACT(EPOCH FROM (NOW() - updated_at)) as inactive_seconds
FROM background_tasks
WHERE status IN ('PENDING', 'PROCESSING')
    AND created_at < NOW() - INTERVAL '5 minutes'
ORDER BY created_at DESC
LIMIT 10;
"""

    file_path = "database_diagnosis_queries.sql"
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(sql_content)
        safe_print(f"\n[成功] SQL查询已保存到: {file_path}")
        safe_print(f"      可以直接复制到数据库客户端执行")
    except Exception as e:
        safe_print(f"\n[警告] 无法保存SQL查询到文件: {e}")
        safe_print(f"      请手动复制上面的查询语句")

def main():
    """主函数"""
    try:
        generate_sql_queries()
        save_sql_to_file()

        safe_print("\n" + "=" * 80)
        safe_print("下一步行动")
        safe_print("=" * 80)
        safe_print("\n1. 连接到Render PostgreSQL数据库")
        safe_print("2. 执行生成的SQL查询（或使用database_diagnosis_queries.sql文件）")
        safe_print("3. 记录查询结果")
        safe_print("4. 根据诊断建议分析问题")
        safe_print("5. 修复发现的问题")

        return 0
    except Exception as e:
        safe_print(f"\n[错误] 生成SQL查询时出错: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())