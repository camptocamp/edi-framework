# Configure

Configure this behavior on `edi.configuration` records.

## 1. Enable activity creation

Activate the option that enables activity creation for exchange errors.

## 2. Select triggering states

Choose which exchange states should create activities (for example, technical error states relevant to your flow).

## 3. Optional: restrict by model

If needed, set a target model filter so activities are only created for selected models.

## 4. Define assignee strategy

Pick how assignees are computed.

- Dynamic strategy: assignee is resolved by module logic.
- Fixed strategy: set a fixed user to receive activities.

## 5. Select activity type

Choose the activity type to create (for example, a to-do style activity used by your operations team).

## 6. Configure deduplication marker

Set the deduplication marker template.

Use a marker that is stable for the same functional error so duplicates are prevented while still creating new activities for distinct issues.

## Recommendation

Define business-specific configuration data in each integration module.
