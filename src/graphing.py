from typing import Iterator
from datetime import datetime, timedelta
from io import BytesIO

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from sqlmodel import select, Session

from src.config import config as CONFIG
from src.models import Temperature

async def get_n_days(n_days,engine) -> dict[str, list[dict[str, int | float]]]:
    """
    Queries and formats data from Temperature table for graphing.

    Features:
    - retrieves all temperature data and groups by device_id
    - formats data for plotting, including timestamp seconds to days since-epoch

    Parameters:
    - n_days: data period, `n_days` days to now
    """

    since_when = datetime.timestamp(
        datetime.now(tz = CONFIG.tz) - timedelta(days=n_days)
    )
    query = select(Temperature)
    query = query.where(Temperature.timestamp > since_when)
    with Session(engine) as session:
        results: list[Temperature] = session.exec(query).all()
    points = list(sorted(results, key=lambda p: p.timestamp))
    devices = set(p.device_id for p in points)
    return {
        d: [
            {
                'd': p.timestamp / 86400, # convert from seconds to days
                't': p.temperature
            }
            for p in points if p.device_id == d
        ]
        for d in devices
    }

async def graph_n_days(dataset: dict[str, list[dict]]):
    """
    Graphs temperature history by device.
    
    Parameter a dict with structure:
        {device1: [{d: datetime, t: temperature},{...}], ...}

    Returns BytesIO object containing plot in png format.
    """
    # set up plot, axes
    fig, ax = plt.subplots(figsize=(8, 5))

    # plot data
    # format_iter: Iterator = iter(['b-','r-','g-','b--','r--','g--'])
    color_iter: Iterator = iter(['b','r','g'])

    for device_id,points in dataset.items():
        # couldn't get this to work
        # ax.plot(
        #     'd',
        #     't',
        #     fmt = next(format_iter),
        #     data = d
        # )
        dt = [p.get('d') for p in points]
        temp = [p.get('t') for p in points]
        plt.plot(
            dt,
            temp,
            color=next(color_iter), 
            marker='v',
            # markerfacecolor=color,
            # markeredgecolor=color,
            label = device_id,
            linestyle = '-'
        )

    # format figure
    ax.set_xlabel('date-time')    
    ax.set_ylabel('temperature')    
    ax.tick_params(axis='x', labelrotation=40)    
    locator = mdates.AutoDateLocator(tz = CONFIG.tz)
    formatter = mdates.ConciseDateFormatter(locator, tz = CONFIG.tz)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    ax.legend()
    plt.tight_layout()

    # save to memory
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=300) # ignore error BytesIO not accepted type is incorrect
    buffer.seek(0) # goes back to start of file
    return buffer