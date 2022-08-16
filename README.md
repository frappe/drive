<div align="center" markdown="1">

<img src=".github/logo.svg" alt="Frappe Drive logo" width="260"/>

#### **An easy to use, document sharing and management solution.**

</div>

---

## Preview

#### Upload and store documents across platforms

<img src=".github/home.png" alt="FD home page"/>


#### Share documents with others

<img src=".github/share.png" alt="FD sharing"/>

#### Access documents shared with you

<img src=".github/shared-with-me.png" alt="FD shared with me page"/>

---

## Installation

### Local

To setup the repository locally follow the steps mentioned below:

1. Install bench and set up a `frappe-bench` directory by following the [installation steps](https://frappeframework.com/docs/user/en/installation).

1. Once you're in the `frappe-bench` directory, start the server
    ```sh
    $ bench start
    ```

1. In a separate terminal instance, but same directory, get the Drive app
    ```sh
    $ bench get-app https://github.com/frappe/drive
    ```
1. Create a new site
    ```sh
    $ bench new-site drive.site
    ```

1. Map your site to localhost
    ```sh
    $ bench --site drive.site add-to-hosts
    ```

1. Install the app onto your site
    ```sh
    $ bench --site drive.site install-app drive
    ```

1. Start the frontend development server
    ```sh
    $ cd apps/drive && yarn dev
    ```

1. Finally, open the URL http://drive.site:8000/drive in your browser to see the app running.

---

## Contributions and Community

There are many ways you can contribute even if you don't code:

1. You can start by giving a star to this repository!
1. If you find any issues, even if it is a typo, you can [raise an issue](https://github.com/frappe/drive/issues/new) to inform us.

If you want to contribute code then you can fork this repo, make changes and raise a PR. ([see how to](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork))

---

## License

[GNU Affero General Public License v3.0](LICENSE)