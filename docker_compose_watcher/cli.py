import click
from .main import main


@click.command()
@click.option("--file", default=None)
@click.option("--timeout", default=5)
@click.help_option('-h', )
@click.help_option('--help', )
@click.argument("service_names", nargs=-1)
def cli(file, service_names, timeout):
    # print(file, service_names, timeout)
    main(file=file, service_names=list(service_names), timeout=timeout)
