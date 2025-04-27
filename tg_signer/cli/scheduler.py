import asyncio
import logging
import click
from click import Group

from tg_signer.core import UserScheduler
from .signer import tg_signer

def get_scheduler(task_name, ctx_obj: dict):
    scheduler = UserScheduler(
        task_name=task_name,
        account=ctx_obj["account"],
        proxy=ctx_obj["proxy"],
        session_dir=ctx_obj["session_dir"],
        workdir=ctx_obj["workdir"],
        session_string=ctx_obj["session_string"],
        in_memory=ctx_obj["in_memory"],
    )
    return scheduler

@tg_signer.group(name="scheduler", help="配置和运行定时任务")
@click.pass_context
def tg_scheduler(ctx: click.Context):
    logger = logging.getLogger("tg-signer")
    if ctx.invoked_subcommand in ["run"]:
        if proxy := ctx.obj.get("proxy"):
            logger.info(
                "Using proxy: %s"
                % f"{proxy['scheme']}://{proxy['hostname']}:{proxy['port']}"
            )
        logger.info(f"Using account: {ctx.obj['account']}")

tg_scheduler: Group

@tg_scheduler.command(name="reconfig", help="重新配置定时任务")
@click.argument("task_name", nargs=1, default="my_scheduler")
@click.pass_obj
def reconfig(obj, task_name):
    scheduler = get_scheduler(task_name, obj)
    scheduler.reconfig()
    logger = logging.getLogger("tg-signer")
    logger.info(f"任务 '{task_name}' 已重新配置")

@tg_scheduler.command(name="schedule_messages", help="定时发送消息到多个频道")
@click.argument("task_name", nargs=1, default="my_scheduler")
@click.option(
    "--channels",
    "-c",
    multiple=True,
    required=True,
    help="要发送消息的频道ID，支持多个",
)
@click.option(
    "--num_messages",
    "-n",
    type=str,
    required=True,
    help="每个频道发送的消息数范围，格式为'频道ID:最小消息数:最大消息数'，支持多个",
)
@click.option(
    "--message_length",
    "-l",
    type=str,
    required=True,
    help="每条消息的长度范围，格式为'频道ID:最小长度:最大长度'，支持多个",
)
@click.pass_obj
def schedule_messages(obj, task_name, channels, num_messages, message_length):
    # 解析消息数范围和消息长度范围
    num_messages_dict = {}
    for item in num_messages:
        channel_id, num_min, num_max = item.split(':')
        num_messages_dict[channel_id] = (int(num_min), int(num_max))
    
    message_length_dict = {}
    for item in message_length:
        channel_id, length_min, length_max = item.split(':')
        message_length_dict[channel_id] = (int(length_min), int(length_max))
    
    scheduler = get_scheduler(task_name, obj)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        scheduler.schedule_messages_with_ai(channels, num_messages_dict, message_length_dict)
    )