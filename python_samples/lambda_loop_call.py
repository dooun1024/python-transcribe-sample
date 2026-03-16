import boto3
import json
import math

lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    # --- 1. 获取业务数据 ---
    # 假设你已经从 S3 读取了数据并转成了 chunks 数组
    # chunks = get_data_from_s3() 
    chunks = list(range(2500))  # 示例数据：2500条
    
    total_count = len(chunks)
    batch_size = 1000
    
    # --- 2. 计算总步数 (仅在第一次或每轮重新确认) ---
    # 使用 math.ceil 确保即便有余数也会多计一步
    all_steps = math.ceil(total_count / batch_size)
    
    # 从 event 获取当前步骤，如果没有则默认为 1（EventBridge 首次触发）
    current_step = event.get('current_step', 1)

    print(f"当前进度: {current_step}/{all_steps} (总数据量: {total_count})")

    # --- 3. 截取并处理当前批次 ---
    start_idx = (current_step - 1) * batch_size
    end_idx = start_idx + batch_size
    current_batch = chunks[start_idx:end_idx]
    
    # 执行业务逻辑
    if current_batch:
        print(f"正在处理第 {start_idx} 到 {min(end_idx, total_count)} 条数据")
        # do_business_logic(current_batch)

    # --- 4. 递归调用判定 ---
    if all_steps > 1 and current_step < all_steps:
        # 封装下一次调用的参数
        next_event = event.copy()
        next_event['current_step'] = current_step + 1
        next_event['all_steps'] = all_steps
        
        print(f"准备进入下一轮: 第 {current_step + 1} 步")
        
        lambda_client.invoke(
            FunctionName=context.function_name,
            InvocationType='Event', # 异步调用
            Payload=json.dumps(next_event)
        )
    else:
        print("达到总步数或只有一步，执行完毕，退出循环。")

    return {
        'statusCode': 200,
        'body': json.dumps(f"Step {current_step} finished")
    }
