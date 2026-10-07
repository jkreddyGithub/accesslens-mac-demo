# AccessLens Entitlement Review Demo

A packaged Mac demo for reviewing synthetic access data. The demo records review
decisions locally and does not change real access.

## Requirements

- Java 17 or newer
- macOS

## Run the demo

From this folder, run:

```sh
java -version
java -jar access-review-demo.jar
```

Keep the terminal open and visit <http://localhost:8080>.

Demo sign-in credentials and alternate-port instructions are in
[START-HERE.txt](./START-HERE.txt).

If port 8080 is already in use, start the app on port 8082:

```sh
java -jar access-review-demo.jar --server.port=8082
```

Then visit <http://localhost:8082>.

## Data and source

Review data is saved locally in the `data` folder, which is intentionally
excluded from this repository. This is a demo build; the complete source and
interview documentation are distributed separately.

Use synthetic data only. Do not use these demo credentials or this application
for production access reviews.
