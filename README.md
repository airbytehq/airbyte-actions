# Airbyte Actions Plugin

This is the Airbyte Actions Plugin. It provides additional functionality for the `aircmd` CLI.

## Installation

To install the plugin, run the following command:

```
aircmd plugin install airbyte_actions
```

## Usage

Once the plugin is installed, you can use the following command to list all available commands in the plugin:

```
aircmd actions --help
```

You should see a list of all available commands in the `airbyte_actions` plugin.

To run a specific command, simply use the following format:

```
aircmd actions <command>
```

Replace `<command>` with the name of the command you want to run.

## Available Commands

The following commands are available in the `airbyte_actions` plugin:

- `command1`: The first command in the plugin.
- `command2`: The second command in the plugin.
- `command3`: The third command in the plugin.

## Development

To get started with developing the `airbyte_actions` plugin, follow these steps:

1. Clone this repository to your local machine.
2. Install the required dependencies using Poetry:

```
poetry install
```

3. Create a new branch for your changes:

```
git checkout -b my-new-feature
```

4. Make your changes to the code.
5. Run tests to make sure everything is working:

```
poetry run pytest
```

6. Commit your changes:

```
git commit -am 'Add some feature'
```

7. Push your changes to your fork:

```
git push origin my-new-feature
```

8. Create a pull request for your changes.
