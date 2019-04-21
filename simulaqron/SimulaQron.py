#!/usr/bin/env python3
import os
import time
import click
import logging
from daemons.prefab import run

from simulaqron.network import Network
from simulaqron.settings import simulaqron_settings
from simulaqron.toolbox import manage_nodes

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])
PID_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".simulaqron_pids")


class SimulaQronDaemon(run.RunDaemon):
    def __init__(self, pidfile, name=None, nrnodes=None, nodes=None, topology=None):
        super().__init__(pidfile=pidfile)
        self.name = name
        self.nrnodes = nrnodes
        self.nodes = nodes
        self.topology = topology

    def run(self):
        """Starts all nodes defined in netsim's config directory."""

        if self.nrnodes or self.nodes or self.topology:
            if self.nodes:
                nodes = self.nodes.split(",")
            else:
                nodes = []

            if self.nrnodes and (self.nrnodes > len(nodes)):
                nodes += ["Node{}".format(i) for i in range(self.nrnodes - len(nodes))]
        else:
            nodes = self.nodes

        network = Network(name=self.name, nodes=nodes, topology=self.topology)
        network.start()

        while True:
            time.sleep(0.1)


@click.group(context_settings=CONTEXT_SETTINGS)
def cli():
    """Command line interface for interacting with SimulaQron."""
    pass

#################
# start command #
#################


@cli.command()
@click.option(
    "--name",
    help="Give the network a name to be able to start multiple (default: default)",
    type=click.STRING,
    default=None,
)
@click.option(
    "-N",
    "--nrnodes",
    help="Number of nodes to start \n(WARNING: overwites existing config files)",
    type=click.INT,
    default=None,
)
@click.option(
    "-n",
    "--nodes",
    help="Comma separated list of nodes to start \n(WARNING: overwites existing config files)",
    type=click.STRING,
    default=None,
)
@click.option(
    "-t",
    "--topology",
    help="Topology of network \n(WARNING: overwites existing config files)",
    type=click.STRING,
    default=None,
)
def start(name, nrnodes, nodes, topology):
    """Starts a network with the given parameters or from config files."""
    manage_nodes.setup_cqc_files()
    if name is None:
        name = "default"
    pidfile = os.path.join(PID_FOLDER, "simulaqron_network_{}.pid".format(name))
    if os.path.exists(pidfile):
        logging.warning("Network with name {} is already running".format(name))
        return
    d = SimulaQronDaemon(pidfile=pidfile, name=name, nrnodes=nrnodes, nodes=nodes, topology=topology)
    d.start()

###############
# stop command #
###############


@cli.command()
@click.option(
    "--name",
    help="Stop the network with then a given name (default: default)",
    type=click.STRING,
    default=None,
)
def stop(name):
    """Stops a network."""
    if name is None:
        name = "default"
    pidfile = os.path.join(PID_FOLDER, "simulaqron_network_{}.pid".format(name))
    if not os.path.exists(pidfile):
        logging.warning("Network with name {} is not running".format(name))
        return
    d = SimulaQronDaemon(pidfile=pidfile)
    d.stop()

#################
# reset command #
#################


@cli.command()
def reset():
    """Resets simulaqron"""
    for entry in os.listdir(PID_FOLDER):
        if entry.endswith(".pid"):
            pidfile = os.path.join(PID_FOLDER, entry)
            d = SimulaQronDaemon(pidfile=pidfile)
            d.stop()
            if os.path.exists(pidfile):
                os.remove(pidfile)


###############
# set command #
###############


@cli.group()
def set():
    """Change a setting"""
    pass


@set.command()
def default():
    """Sets all settings back to default"""
    simulaqron_settings.default_settings()


@set.command()
@click.argument('value', type=click.Choice(["stabilizer", "projectq", "qutip"]))
def backend(value):
    """The backend to use (stabilizer, projectq, qutip)."""
    simulaqron_settings.set_setting("BACKEND", "backend", value)


@set.command()
@click.argument('value', type=int)
def max_qubits(value):
    """Max virt-qubits per node and max sim-qubits per register."""
    simulaqron_settings.set_setting("BACKEND", "maxqubits_per_node", str(value))


@set.command()
@click.argument('value', type=int)
def max_registers(value):
    """How many registers a node can hold."""
    simulaqron_settings.set_setting("BACKEND", "maxregs_per_node", str(value))


@set.command()
@click.argument('value', type=float)
def conn_retry_time(value):
    """If setup fails, how long to wait until a retry."""
    simulaqron_settings.set_setting("BACKEND", "waittime", str(value))


@set.command()
@click.argument('value', type=float)
def recv_timeout(value):
    """When receiving a qubit or EPR pair, how long to wait until raising a timeout."""
    simulaqron_settings.set_setting("BACKEND", "recvtimeout", str(value))
    simulaqron_settings.set_setting("BACKEND", "recveprtimeout", str(value))


@set.command()
@click.argument('value', type=float)
def recv_retry_time(value):
    """When receiving a qubit or EPR pair, how long to wait between checks of whether a qubit is received."""
    simulaqron_settings.set_setting("BACKEND", "waittimerecv", str(value))


@set.command()
@click.argument('value', type=click.Choice(["debug", "info", "warning", "error", "critical"]))
def log_level(value):
    """Log level for both backend and frontend."""
    simulaqron_settings.set_setting("BACKEND", "loglevel", value)
    simulaqron_settings.set_setting("FRONTEND", "loglevel", value)


@set.command()
@click.argument('value', type=str)
def topology_file(value):
    """The path to the topology file to be used, can be ""."""
    simulaqron_settings.set_setting("BACKEND", "topology_file", value)


@set.command()
@click.argument('value', type=str)
def app_file(value):
    """The path to the topology file to be used, can be ""."""
    simulaqron_settings.set_setting("BACKEND", "app_file", value)


@set.command()
@click.argument('value', type=str)
def cqc_file(value):
    """The path to the topology file to be used, can be ""."""
    simulaqron_settings.set_setting("BACKEND", "cqc_file", value)


@set.command()
@click.argument('value', type=str)
def vnode_file(value):
    """The path to the topology file to be used, can be ""."""
    simulaqron_settings.set_setting("BACKEND", "vnode_file", value)


@set.command()
@click.argument('value', type=str)
def nodes_file(value):
    """The path to the topology file to be used, can be ""."""
    simulaqron_settings.set_setting("BACKEND", "nodes_file", value)


@set.command()
@click.argument('value', type=click.Choice("on", "off"))
def noisy_qubits(value):
    """Whether qubits should be noisy (on/off)"""
    if value == "on":
        simulaqron_settings.set_setting("BACKEND", "noisy_qubits", 'True')
    else:
        simulaqron_settings.set_setting("BACKEND", "noisy_qubits", 'False')


@set.command()
@click.argument('value', type=float)
def t1(value):
    """The effective T1 to be used for noisy qubits"""
    simulaqron_settings.set_setting("BACKEND", "t1", str(value))

###############
# get command #
###############


@cli.group()
def get():
    """Get a setting"""
    pass


@get.command()
def backend():
    """The backend to use (stabilizer, projectq, qutip)."""
    print(simulaqron_settings.backend)


@get.command()
def max_qubits():
    """Max virt-qubits per node and max sim-qubits per register."""
    print(simulaqron_settings.max_qubits)


@get.command()
def max_registers():
    """How many registers a node can hold."""
    print(simulaqron_settings.max_registers)


@get.command()
def conn_retry_time():
    """If setup fails, how long to wait until a retry."""
    print(simulaqron_settings.conn_retry_time)


@get.command()
def recv_timeout():
    """When receiving a qubit or EPR pair, how long to wait until raising a timeout."""
    print(simulaqron_settings.recv_timeout)


@get.command()
def recv_retry_time():
    """When receiving a qubit or EPR pair, how long to wait between checks of whether a qubit is received."""
    print(simulaqron_settings.recv_retry_time)


@get.command()
def log_level():
    """Log level for both backend and frontend."""
    print(simulaqron_settings.log_level)


@get.command()
def topology_file():
    """The path to the topology file to be used, can be ""."""
    print(simulaqron_settings.topology_file)


@get.command()
def app_file():
    """The path to the app file to be used, can be ""."""
    print(simulaqron_settings.app_file)


@get.command()
def cqc_file():
    """The path to the cqc file to be used, can be ""."""
    print(simulaqron_settings.cqc_file)


@get.command()
def vnode_file():
    """The path to the vnode file to be used, can be ""."""
    print(simulaqron_settings.vnode_file)


@get.command()
def nodes_file():
    """The path to the nodes file to be used, can be ""."""
    print(simulaqron_settings.nodes_file)


@get.command()
def noisy_qubits():
    """Whether qubits should be noisy (on/off)"""
    if simulaqron_settings.noisy_qubits == 'True':
        print("on")
    else:
        print("off")


@get.command()
def t1():
    """The effective T1 to be used for noisy qubits"""
    print(simulaqron_settings.t1)

###############
# node command #
###############


@cli.group()
def nodes():
    """
    Manage the nodes in the simulated network.

    NOTE: This needs to be done before starting the network.
    """
    pass


@nodes.command()
@click.argument('name', type=str)
@click.option('--hostname', type=str,
              help="The host name of the node, e.g. localhost (default) or 192.168.0.1")
@click.option('--app-port', type=int,
              help="Port number for the application.\n \
                    If not specified a random unused port between 8000 and 9000 will be used.")
@click.option('--cqc-port', type=int,
              help="Port number for the cqc server.\n \
                    If not specified a random unused port between 8000 and 9000 will be used.")
@click.option('--vnode-port', type=int,
              help="Port number for the virtual node.\n \
                    If not specified a random unused port between 8000 and 9000 will be used.")
@click.option('--neighbors', type=str,
              help="The neighbors of the node in the network seperated by ',' (no space).\n \
                    For example '--neighbors Bob,Charlie,David'.\n \
                    If not specified all current nodes in the network will be neighbors.")
def add(name, hostname=None, app_port=None, cqc_port=None, vnode_port=None, neighbors=None):
    """
    Add a node to the network.

    NAME: The name of the node, e.g. Alice

    HOSTNAME: The host name of the node, e.g. localhost or 192.168.0.1
    """
    if neighbors is not None:
        neighbors = neighbors.split(',')
        neighbors = [neighbor.strip() for neighbor in neighbors]
    manage_nodes.add_node(name, hostname=hostname, app_port=app_port, cqc_port=cqc_port, vnode_port=vnode_port,
                          neighbors=neighbors)


@nodes.command()
@click.argument('name', type=str)
def remove(name):
    """
    Remove a node to the network.

    NAME: The name of the node, e.g. Alice
    """
    manage_nodes.remove_node(name)
    pass


@nodes.command()
def default():
    """
    Sets the default nodes of the network.

    The default network consists of the five nodes:
    Alice, Bob, Charlie, David, Eve
    """
    manage_nodes.set_default_nodes()


@nodes.command()
def get():
    """Get the current nodes of the network."""
    nodes = manage_nodes.get_nodes()
    print(("{} " * len(nodes))[:-1].format(*nodes))


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s:%(levelname)s:%(message)s",
        level=simulaqron_settings.log_level,
    )
    cli()
