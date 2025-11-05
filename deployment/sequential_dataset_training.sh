        fi

        TOTAL_STEPS=$((TOTAL_STEPS + STEPS_PER_DATASET))
        print_info "Total training steps so far: $TOTAL_STEPS"
        print_success "✓ Stage $DATASET_NUM complete. Ready for next stage."
    else
        print_error "Training failed on $DATASET_NAME (exit code: $TRAIN_EXIT_CODE)"
        print_error "Sequential training stopped. Not proceeding to next dataset."
        exit 1
    fi

    echo ""
done

# Change back to project root for final summary
cd "$PROJECT_ROOT" || {
    print_error "Failed to change back to project root"
    exit 1
}

print_header "Sequential Training Complete!"
print_success "Trained on ${#DATASETS[@]} datasets"
print_success "Total training steps: $TOTAL_STEPS"
print_success "Final model saved to: $PREVIOUS_CHECKPOINT"

if [ "$WANDB_ENABLE" = "true" ]; then
    print_info "Check WandB for training metrics and comparisons"
fi

echo ""
print_info "To evaluate the final model, run:"
echo "lerobot-eval --policy.path=$PREVIOUS_CHECKPOINT"
echo "or"
echo "lerobot-eval --policy.path=$HUB_REPO_ID"
echo ""

print_header "Training Summary"
echo "Sequential training allows the model to:"
echo "  ✓ Build upon previously learned behaviors"
echo "  ✓ Incrementally adapt to new data"
echo "  ✓ Potentially achieve better generalization"
echo ""
echo "The final model has been pushed to: https://huggingface.co/$HUB_REPO_ID"
echo ""
echo "Compare this with multi-dataset training (all datasets together) to see"
echo "which approach works better for your use case!"
echo ""
