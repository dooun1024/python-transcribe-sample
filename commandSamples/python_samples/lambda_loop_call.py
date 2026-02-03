import boto3
import json
import time


lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    # 1. 初始化参数（从 event 中读取，若没有则设为默认值）
    current_step = event.get('current_step', 1)
    all_steps = event.get('all_steps', None)  # 初始为 None，由业务逻辑计算
    
    print(f"开始执行第 {current_step} 步...")

    # --- 2. 执行你的业务逻辑 ---
    # 假设这里计算出了总步数
    if all_steps is None:
        all_steps = 3  # 示例：假设业务决定总共跑10步
    
    # 执行具体的业务操作...
    # do_something(current_step)
    # -----------------------
    time.sleep(5)

    # 3. 判定是否需要循环调用
    if current_step < all_steps:
        # 更新参数传递给下一次调用
        next_event = event.copy()
        next_event['current_step'] = current_step + 1
        next_event['all_steps'] = all_steps
        
        print(f"正在触发下一次调用: {current_step + 1}/{all_steps}")
        
        # 异步调用自身 (Recursive Call)
        lambda_client.invoke(
            FunctionName=context.function_name,
            InvocationType='Event',  # 异步触发，不等待返回
            Payload=json.dumps(next_event)
        )
    else:
        print("所有步骤已完成，退出循环。")
        
    return {
        'statusCode': 200,
        'body': f'Step {current_step} processed.'
    }