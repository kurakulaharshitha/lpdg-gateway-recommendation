# AI Usage

I used AI tools as a development assistant during this challenge.

## What I used AI for

I used AI to help with:

- understanding the challenge requirements
- breaking the project into smaller implementation steps
- reviewing the supplied 3-sigma baseline
- suggesting a clean FastAPI project structure
- drafting initial unit and API test cases
- reviewing error-handling ideas
- improving documentation wording
- identifying areas of the baseline that deserved closer inspection

I reviewed and ran all generated or suggested code before keeping it in the project.

## What I did not delegate to AI

I did not treat AI output as automatically correct.

I manually:

- ran the supplied baseline
- validated `predictions.csv`
- tested the API endpoints
- ran the full pytest suite
- tested the Docker build
- ran the service inside Docker
- validated the Docker-generated `predictions.csv`
- checked the behaviour of future-data filtering

## One thing AI got wrong

During development, AI initially suggested a test named as if it proved that the `/run` endpoint cleared the telemetry cache.

The first version of that test only checked that `/run` returned a successful response and wrote 120 rows. It did not actually prove that fresh telemetry was reloaded.

I noticed that the test name claimed more than the test verified.

I replaced it with a stronger regression test that:

1. places old telemetry in the cache,
2. simulates fresh telemetry becoming available,
3. calls `/run`,
4. verifies that the cached copy is cleared,
5. verifies that the fresh data is passed into prediction generation.

This was a useful reminder that AI-generated tests can look convincing while still failing to verify the behaviour they claim to test.

## How I used AI responsibly

I treated AI suggestions as drafts rather than final answers.

For each important change I:

- read the code,
- understood what it was doing,
- ran it locally,
- tested failure cases,
- and kept only behaviour I could explain.

The final implementation and submission decisions are my responsibility.